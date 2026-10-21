import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from app.application.dto.reportes import (
    ACCESO_TOTAL, AlertaAcumulacion, FiltroReportes, MAX_ESTUDIANTES_POR_INCIDENTE, ReporteCreado,
)
from app.application.ports.notificador import NotificadorPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import periodo_vigente_o_error
from app.application.use_cases.llamadas._comun import tutor_principal
from app.application.use_cases.reportes._comun import alertas_de, enriquecer, registrar
from app.domain.entities.ciclo_acumulacion import CicloAcumulacion
from app.domain.entities.intento_llamada import IntentoLlamada
from app.domain.entities.reporte import Reporte
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_acumulacion import UMBRAL_ACUMULACION, alcanza_umbral, contables
from app.domain.value_objects.estado_reporte import EstadoReporte, TipoEventoReporte
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
from app.domain.value_objects.gravedad import Gravedad

log = logging.getLogger(__name__)
TOLERANCIA_FUTURO = timedelta(minutes=5)


class CrearReportes:
    """Genera un reporte por estudiante (los de un mismo suceso comparten `incidente_id`).

    Todos entran directamente a revisión de Orientación. Los Grave y Muy grave además alertan
    a Subdirección de inmediato, sin esperar la acumulación.
    """

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto, notificador: NotificadorPuerto):
        self._uow = uow
        self._reloj = reloj
        self._notificador = notificador

    def ejecutar(
        self,
        actor: Usuario,
        estudiante_ids: List[int],
        tipo_incidencia_id: int,
        descripcion: str,
        gravedad: Gravedad,
        descripcion_otro: Optional[str] = None,
        fecha_hora_incidente: Optional[datetime] = None,
    ) -> List[ReporteCreado]:
        ids = list(dict.fromkeys(estudiante_ids))
        if not 1 <= len(ids) <= MAX_ESTUDIANTES_POR_INCIDENTE:
            raise ReglaDeNegocioViolada(
                f"Indica de 1 a {MAX_ESTUDIANTES_POR_INCIDENTE} estudiantes por incidente."
            )
        gravedad = Gravedad(gravedad)
        ahora = self._reloj.ahora()
        fecha = self._reloj.localizar(fecha_hora_incidente) if fecha_hora_incidente else ahora
        if fecha > ahora + TOLERANCIA_FUTURO:
            raise ReglaDeNegocioViolada("La fecha del incidente no puede ser futura.")

        with self._uow as uow:
            tipo = uow.tipos_incidencia.obtener_por_id(tipo_incidencia_id)
            if tipo is None:
                raise NoEncontrado("Tipo de incidencia no encontrado.")
            if not tipo.activo:
                raise ReglaDeNegocioViolada("Ese tipo de incidencia está desactivado.")
            otro = (descripcion_otro or "").strip()
            if tipo.es_otro and not otro:
                raise ReglaDeNegocioViolada("Describe el tipo de incidencia (opción 'Otro').")
            otro = otro if tipo.es_otro else None

            periodo = periodo_vigente_o_error(uow)
            estudiantes = uow.estudiantes.obtener_por_ids(ids)
            if len(estudiantes) != len(ids):
                raise NoEncontrado("Alguno de los estudiantes no existe.")
            inactivos = [e.numero_control for e in estudiantes.values() if e.estatus != EstatusEstudiante.ACTIVO]
            if inactivos:
                raise ReglaDeNegocioViolada("Estudiantes no activos: " + ", ".join(inactivos) + ".")
            inscripciones = uow.inscripciones.obtener_de_estudiantes(ids, periodo.id)
            sin_grupo = [estudiantes[i].numero_control for i in ids if i not in inscripciones]
            if sin_grupo:
                raise ReglaDeNegocioViolada(
                    "Sin grupo en el periodo vigente: " + ", ".join(sin_grupo) + "."
                )

            incidente_id = str(uuid.uuid4())
            creados, guardados, ciclos = [], [], {}
            for eid in ids:
                ciclo = ciclos.get(eid) or uow.ciclos.obtener_abierto(eid)
                if ciclo is None:  # primer reporte del estudiante, o el anterior ciclo se cerró con una sanción
                    ciclo = uow.ciclos.guardar(CicloAcumulacion(
                        estudiante_id=eid, numero=uow.ciclos.siguiente_numero(eid), fecha_inicio=ahora))
                ciclos[eid] = ciclo
                numero = uow.reportes.siguiente_numero_folio(ahora.year)
                reporte = Reporte(
                    estudiante_id=eid, inscripcion_id=inscripciones[eid].id, creado_por=actor.id,
                    tipo_incidencia_id=tipo.id, descripcion=descripcion, fecha_hora_incidente=fecha,
                    gravedad=gravedad, incidente_id=incidente_id, descripcion_otro=otro,
                    folio=f"RPT-{ahora.year}-{numero:04d}", creado_en=ahora, ciclo_id=ciclo.id,
                )
                reporte.transicionar(EstadoReporte.EN_REVISION_ORIENTACION)
                uow.reportes.guardar(reporte)
                registrar(uow, reporte.id, TipoEventoReporte.CREACION, actor.id, ahora, valor_nuevo=reporte.folio)
                registrar(uow, reporte.id, TipoEventoReporte.ESTADO, actor.id, ahora, campo="estado",
                          valor_anterior=EstadoReporte.CREADO.value, valor_nuevo=reporte.estado.value,
                          comentario="Turnado automáticamente a Orientación Educativa.")
                # Cada reporte genera una llamada pendiente al padre o tutor principal.
                principal = tutor_principal(uow.tutores_legales.listar_por_estudiante(eid))
                if principal is not None:
                    uow.llamadas.guardar(IntentoLlamada(reporte_id=reporte.id, tutor_legal_id=principal.id, creado_en=ahora))
                guardados.append(reporte)
                e = estudiantes[eid]
                creados.append(ReporteCreado(reporte.id, reporte.folio, eid, e.numero_control, e.nombre_completo))
            alertas = alertas_de(uow, guardados) if gravedad.escala_a_subdireccion else []
            acumulaciones = self._alertas_de_acumulacion(uow, guardados, ciclos)
            uow.commit()

        # Fuera de la transacción: un fallo al avisar no debe deshacer el reporte.
        for enviar, datos in ((self._notificador.alertar_gravedad_a_subdireccion, alertas),
                              (self._notificador.alertar_acumulacion_a_subdireccion, acumulaciones)):
            if datos:
                try:
                    enviar(datos)
                except Exception:  # noqa: BLE001
                    log.exception("No se pudo enviar la alerta a Subdirección")
        return creados

    @staticmethod
    def _alertas_de_acumulacion(uow, guardados, ciclos):
        """Estudiantes que con este reporte llegan (o siguen) en 3 o más reportes contables del ciclo."""
        listados = {l.reporte.estudiante_id: l for l in enriquecer(uow, guardados)}
        alertas = []
        for eid, ciclo in ciclos.items():
            reportes = contables(uow.reportes.listar(FiltroReportes(
                acceso=ACCESO_TOTAL, ciclo_id=ciclo.id, solo_contables=True, limite=1000)))
            if alcanza_umbral(len(reportes)):
                l = listados[eid]
                alertas.append(AlertaAcumulacion(
                    estudiante_id=eid, estudiante=l.estudiante, numero_control=l.numero_control, grupo=l.grupo_clave,
                    total=len(reportes), umbral=UMBRAL_ACUMULACION, folios=sorted(r.folio for r in reportes)))
        return alertas
