"""Indicadores y gráficas de la página de inicio, ya recortados a lo que cada usuario puede ver."""
from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Tuple

from app.application.dto.dashboard import RANGOS, Dashboard, EstudianteEnRiesgo
from app.application.dto.reportes import FiltroReportes
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.exportaciones.exportar_reportes import ETIQUETA_ESTADO, ETIQUETA_GRAVEDAD, ORDEN_GRAVEDAD
from app.application.use_cases.reportes._comun import acceso_de, enriquecer
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_acumulacion import UMBRAL_ACUMULACION
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_reporte import EstadoReporte

MAX_REPORTES = 5000
TOP = 10
RIESGO_MINIMO = UMBRAL_ACUMULACION - 1  # 2


def _inicio_dia(dia: date, ref: datetime) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=ref.tzinfo)


def _primer_dia_mes(dia: date) -> date:
    return dia.replace(day=1)


def _top(contador: Counter, n: int = TOP) -> List[Tuple[str, int]]:
    return sorted(contador.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


class ObtenerDashboard:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor: Usuario, rango: str = "periodo") -> Dashboard:
        if rango not in RANGOS:
            raise ReglaDeNegocioViolada("El rango debe ser periodo, mes o 30dias.")
        ahora = self._reloj.ahora()
        hoy = ahora.date()
        with self._uow as uow:
            periodo = uow.periodos.obtener_vigente()
            if rango == "periodo" and periodo is None:
                rango = "30dias"  # sin periodo vigente no hay de dónde tomar el rango
            if rango == "periodo":
                desde_d, hasta_d = periodo.fecha_inicio, min(periodo.fecha_fin, hoy)
            elif rango == "mes":
                desde_d, hasta_d = _primer_dia_mes(hoy), hoy
            else:
                desde_d, hasta_d = hoy - timedelta(days=29), hoy
            granularidad = "semana" if (hasta_d - desde_d).days > 62 else "dia"
            base = dict(rango=rango, desde=desde_d, hasta=hasta_d, granularidad=granularidad,
                        periodo_nombre=periodo.nombre if periodo else None)

            acceso = acceso_de(uow, actor)
            if acceso.sin_acceso:
                return Dashboard(alcance="ninguno", **base)

            def listar(**filtro):
                return uow.reportes.listar(FiltroReportes(acceso=acceso, limite=MAX_REPORTES, **filtro))

            en_rango = listar(desde=_inicio_dia(desde_d, ahora), hasta=_inicio_dia(hasta_d + timedelta(days=1), ahora) - timedelta(seconds=1))
            detalle = enriquecer(uow, en_rango)

            inicio_mes = _primer_dia_mes(hoy)
            fin_mes_anterior = inicio_mes - timedelta(days=1)
            mes_actual = len(listar(desde=_inicio_dia(inicio_mes, ahora)))
            mes_anterior = len(listar(
                desde=_inicio_dia(_primer_dia_mes(fin_mes_anterior), ahora), hasta=_inicio_dia(inicio_mes, ahora) - timedelta(seconds=1)))

            gravedad = Counter(ETIQUETA_GRAVEDAD[r.gravedad.value] for r in en_rango)
            ve_todo = tiene_permiso(actor.roles, Permiso.VER_TODOS_LOS_REPORTES)
            pendientes = None
            if ve_todo:
                pendientes = sum(
                    1 for r in listar(sin_llamada_efectiva=True) if r.estado != EstadoReporte.SANCIONADO_CONCLUIDO)
            alertas = (uow.notificaciones.contar_pendientes("SUBDIRECCION")
                       if tiene_permiso(actor.roles, Permiso.VER_ALERTAS) else None)
            riesgo, listos, total_riesgo = self._riesgo(uow, listar)

            return Dashboard(
                alcance="total" if acceso.total else "propio", **base,
                total_rango=len(en_rango), mes_actual=mes_actual, mes_anterior=mes_anterior,
                por_gravedad=[(g, gravedad.get(g, 0)) for g in ORDEN_GRAVEDAD],
                pendientes_llamada=pendientes, alertas_pendientes=alertas,
                en_riesgo=riesgo, listos_para_sancion=listos, total_en_riesgo=total_riesgo,
                serie=self._serie(en_rango, desde_d, hasta_d, granularidad, ahora),
                por_grupo=_top(Counter(d.grupo_clave or "Sin grupo" for d in detalle)),
                por_carrera=_top(Counter(d.carrera_nombre or "Sin carrera" for d in detalle)),
                por_tipo=_top(Counter(d.tipo_incidencia for d in detalle)),
                por_estado=[(ETIQUETA_ESTADO[e], c) for e in EstadoReporte
                            for c in [sum(1 for r in en_rango if r.estado == e)]],
            )

    def _serie(self, reportes, desde: date, hasta: date, granularidad: str, ahora) -> List[Tuple[str, int]]:
        def cubeta(d: date) -> date:
            return d - timedelta(days=d.weekday()) if granularidad == "semana" else d

        cuenta: Dict[date, int] = Counter(cubeta(self._reloj.localizar(r.fecha_hora_incidente).date()) for r in reportes)
        paso = timedelta(days=7 if granularidad == "semana" else 1)
        salida, actual = [], cubeta(desde)
        while actual <= hasta:
            salida.append((actual.isoformat(), cuenta.get(actual, 0)))
            actual += paso
        return salida

    def _riesgo(self, uow, listar):
        """Estudiantes con 2 o más reportes que cuentan en su ciclo abierto (a uno de la sanción por acumulación)."""
        por_ciclo: Dict[Tuple[int, int], list] = {}
        for r in listar(solo_contables=True):
            if r.ciclo_id is not None:
                por_ciclo.setdefault((r.estudiante_id, r.ciclo_id), []).append(r)
        candidatos = []
        for (est_id, ciclo_id), lista in por_ciclo.items():
            if len(lista) < RIESGO_MINIMO:
                continue
            abierto = uow.ciclos.obtener_abierto(est_id)
            if abierto is not None and abierto.id == ciclo_id:
                candidatos.append((est_id, lista))
        if not candidatos:
            return [], 0, 0
        candidatos.sort(key=lambda c: -len(c[1]))
        listos = sum(1 for _, lista in candidatos if len(lista) >= UMBRAL_ACUMULACION)
        visibles = candidatos[:TOP]
        detalle = {d.reporte.estudiante_id: d for d in enriquecer(uow, [lista[0] for _, lista in visibles])}
        riesgo = [EstudianteEnRiesgo(e, detalle[e].estudiante, detalle[e].grupo_clave, len(lista)) for e, lista in visibles]
        return riesgo, listos, len(candidatos)
