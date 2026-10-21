"""Reglas de la acumulación de reportes (sección 2.4 de la especificación)."""
from typing import Iterable, List

from app.domain.entities.reporte import Reporte

UMBRAL_ACUMULACION = 3


def contables(reportes: Iterable[Reporte]) -> List[Reporte]:
    """Cuentan: reportes no cancelados y sin sanción directa (incluye Leves ya atendidos sin sanción
    y Graves/Muy graves que aún no recibieron sanción directa)."""
    return [r for r in reportes if r.es_contable]


def alcanza_umbral(total_contables: int) -> bool:
    return total_contables >= UMBRAL_ACUMULACION
