from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.sancion import Sancion


class SancionRepositorio(ABC):
    @abstractmethod
    def guardar(self, sancion: Sancion) -> Sancion: ...

    @abstractmethod
    def obtener_por_reporte(self, reporte_id: int) -> Optional[Sancion]: ...

    @abstractmethod
    def obtener_por_ciclo(self, ciclo_id: int) -> Optional[Sancion]: ...

    @abstractmethod
    def listar_por_estudiante(self, estudiante_id: int) -> List[Sancion]: ...
