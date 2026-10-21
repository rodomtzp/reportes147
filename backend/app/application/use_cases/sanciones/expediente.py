from app.application.dto.reportes import ACCESO_TOTAL, FiltroReportes
from app.application.dto.sanciones import CicloDetalle, ExpedienteDisciplinario
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import grupo_y_carrera, mapas_academicos
from app.application.use_cases.reportes._comun import enriquecer
from app.application.use_cases.sanciones.vistas import detalle_sancion
from app.domain.exceptions import NoEncontrado
from app.domain.policies.politica_acumulacion import UMBRAL_ACUMULACION
from app.domain.value_objects.origen_sancion import OrigenSancion


class ObtenerExpediente:
    """Historial disciplinario del estudiante en toda su carrera (la autorización se exige en la API)."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, estudiante_id: int) -> ExpedienteDisciplinario:
        with self._uow as uow:
            e = uow.estudiantes.obtener_por_id(estudiante_id)
            if e is None:
                raise NoEncontrado("Estudiante no encontrado.")
            listados = enriquecer(uow, uow.reportes.listar(FiltroReportes(
                acceso=ACCESO_TOTAL, estudiante_id=estudiante_id, incluir_cancelados=True, limite=1000)))
            por_ciclo = {}
            for l in listados:
                por_ciclo.setdefault(l.reporte.ciclo_id, []).append(l)

            actual, anteriores = None, []
            for c in uow.ciclos.listar_por_estudiante(estudiante_id):
                reportes = por_ciclo.get(c.id, [])
                sancion = uow.sanciones.obtener_por_ciclo(c.id)
                detalle = CicloDetalle(c, reportes, sum(1 for r in reportes if r.reporte.es_contable),
                                       detalle_sancion(uow, sancion) if sancion else None)
                if c.abierto:
                    actual = detalle
                else:
                    anteriores.append(detalle)

            vigente = uow.periodos.obtener_vigente()
            insc = uow.inscripciones.obtener(estudiante_id, vigente.id) if vigente else None
            grupos, carreras = mapas_academicos(uow)
            grupo, _ = grupo_y_carrera(grupos, carreras, insc.grupo_id if insc else None)
            directas = [detalle_sancion(uow, s) for s in uow.sanciones.listar_por_estudiante(estudiante_id)
                        if s.origen == OrigenSancion.DIRECTA]
            return ExpedienteDisciplinario(
                estudiante_id=e.id, estudiante=e.nombre_completo, numero_control=e.numero_control, grupo_actual=grupo,
                total_reportes=sum(1 for l in listados if not l.reporte.cancelado), umbral=UMBRAL_ACUMULACION,
                ciclo_actual=actual, ciclos_anteriores=sorted(anteriores, key=lambda c: c.ciclo.numero),
                sanciones_directas=directas,
            )
