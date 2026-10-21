from app.application.dto.llamadas import SeguimientoLlamadas
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.bitacora.registro import registrar_consulta_contacto
from app.application.use_cases.llamadas._comun import llamadas_detalle, mensajes_detalle
from app.application.use_cases.reportes._comun import cargar_reporte
from app.domain.policies.politica_llamadas import resumen_estado_llamada


class ObtenerSeguimientoLlamadas:
    """Vista de trabajo de Orientación (incluye los teléfonos; el permiso se exige en la API)."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, reporte_id: int) -> SeguimientoLlamadas:
        with self._uow as uow:
            reporte = cargar_reporte(uow, reporte_id)
            estudiante = uow.estudiantes.obtener_por_id(reporte.estudiante_id)
            llamadas = llamadas_detalle(uow, reporte_id)
            registrar_consulta_contacto(
                uow, self._reloj, actor_id, estudiante.id, f"Seguimiento de llamadas del reporte {reporte.folio}")
            uow.commit()
            return SeguimientoLlamadas(
                folio=reporte.folio, estudiante=estudiante.nombre_completo,
                estado_llamada=resumen_estado_llamada([l.intento.estado for l in llamadas]).value,
                tutores=uow.tutores_legales.listar_por_estudiante(reporte.estudiante_id),
                llamadas=llamadas, mensajes=mensajes_detalle(uow, reporte_id),
            )
