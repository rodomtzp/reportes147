from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.historial_reporte import HistorialReporte


class HistorialReporteRepositorio(ABC):
    @abstractmethod
    def agregar(self, evento: HistorialReporte) -> HistorialReporte: ...

    @abstractmethod
    def listar_por_reporte(self, reporte_id: int) -> List[HistorialReporte]: ...
