from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.origen_sancion import OrigenSancion

DIAS_MIN, DIAS_MAX = 1, 365


@dataclass
class Sancion:
    """Directa: ligada a un reporte. Por acumulación: ligada al ciclo (cubre todos sus reportes)."""

    tipo_sancion_id: int
    origen: OrigenSancion
    estudiante_id: int
    aplicada_por: int
    aplicada_en: datetime
    reporte_id: Optional[int] = None
    ciclo_id: Optional[int] = None
    dias: Optional[int] = None
    observaciones: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.origen = OrigenSancion(self.origen)
        if self.origen == OrigenSancion.DIRECTA and (self.reporte_id is None or self.ciclo_id is not None):
            raise ReglaDeNegocioViolada("La sanción directa debe ligarse a un reporte.")
        if self.origen == OrigenSancion.ACUMULACION and (self.ciclo_id is None or self.reporte_id is not None):
            raise ReglaDeNegocioViolada("La sanción por acumulación debe ligarse a un ciclo.")
        self.observaciones = (self.observaciones or "").strip() or None
        if self.observaciones and len(self.observaciones) > 1000:
            raise ReglaDeNegocioViolada("Las observaciones no deben exceder 1000 caracteres.")
        if self.dias is not None and not DIAS_MIN <= self.dias <= DIAS_MAX:
            raise ReglaDeNegocioViolada(f"Los días deben estar entre {DIAS_MIN} y {DIAS_MAX}.")
