"""Armado de las vistas de sanciones y acumulación (sin dependencias de los casos de uso de reportes)."""
from dataclasses import replace
from typing import Optional

from app.application.dto.reportes import ACCESO_TOTAL, FiltroReportes
from app.application.dto.sanciones import ResumenAcumulacion, SancionDetalle
from app.domain.entities.reporte import Reporte
from app.domain.entities.sancion import Sancion
from app.domain.policies.politica_acumulacion import UMBRAL_ACUMULACION
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.origen_sancion import OrigenSancion


def detalle_sancion(uow, sancion: Sancion) -> SancionDetalle:
    tipo = uow.tipos_sancion.obtener_por_id(sancion.tipo_sancion_id)
    autor = uow.usuarios.obtener_por_ids([sancion.aplicada_por]).get(sancion.aplicada_por)
    if sancion.origen == OrigenSancion.DIRECTA:
        reporte = uow.reportes.obtener_por_id(sancion.reporte_id)
        folios = [reporte.folio] if reporte else []
    else:
        cubiertos = uow.reportes.listar(FiltroReportes(acceso=ACCESO_TOTAL, ciclo_id=sancion.ciclo_id, solo_contables=True, limite=1000))
        folios = sorted(r.folio for r in cubiertos)
    return SancionDetalle(sancion, tipo.nombre if tipo else "?", autor.nombre if autor else "?", folios)


def sancion_de_reporte(uow, reporte: Reporte, con_observaciones: bool) -> Optional[SancionDetalle]:
    """Sanción que cubre al reporte: la directa, o la del ciclo si se sancionó por acumulación."""
    sancion = uow.sanciones.obtener_por_reporte(reporte.id)
    if sancion is None and reporte.estado == EstadoReporte.SANCIONADO_CONCLUIDO and reporte.ciclo_id and reporte.es_contable:
        sancion = uow.sanciones.obtener_por_ciclo(reporte.ciclo_id)
    if sancion is None:
        return None
    detalle = detalle_sancion(uow, sancion)
    if not con_observaciones:  # quien no es directivo ve el tipo y los días, no las observaciones
        detalle = replace(detalle, sancion=replace(detalle.sancion, observaciones=None))
    return detalle


def resumen_acumulacion(uow, estudiante_id: int) -> Optional[ResumenAcumulacion]:
    ciclo = uow.ciclos.obtener_abierto(estudiante_id)
    if ciclo is None:
        return None
    total = len(uow.reportes.listar(FiltroReportes(acceso=ACCESO_TOTAL, ciclo_id=ciclo.id, solo_contables=True, limite=1000)))
    return ResumenAcumulacion(ciclo.numero, total, UMBRAL_ACUMULACION)
