from abc import ABC, abstractmethod
from typing import List, Optional

from app.application.dto.reportes import AccesoReportes, FiltroReportes
from app.domain.entities.reporte import Reporte


class ReporteRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, reporte_id: int) -> Optional[Reporte]: ...

    @abstractmethod
    def guardar(self, reporte: Reporte) -> Reporte: ...

    @abstractmethod
    def listar(self, filtro: FiltroReportes) -> List[Reporte]:
        """Aplica los filtros y la restricción de acceso (`filtro.acceso`)."""

    @abstractmethod
    def es_visible(self, reporte_id: int, acceso: AccesoReportes) -> bool: ...

    @abstractmethod
    def siguiente_numero_folio(self, anio: int) -> int:
        """Siguiente consecutivo del año (se reinicia cada año). Debe ser seguro ante concurrencia."""
