from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from app.domain.entities.inscripcion import Inscripcion


class InscripcionRepositorio(ABC):
    @abstractmethod
    def obtener(self, estudiante_id: int, periodo_id: int) -> Optional[Inscripcion]: ...

    @abstractmethod
    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Inscripcion]: ...

    @abstractmethod
    def obtener_de_estudiantes(self, ids: Iterable[int], periodo_id: int) -> Dict[int, Inscripcion]: ...

    @abstractmethod
    def listar_por_estudiante(self, estudiante_id: int) -> List[Inscripcion]:
        """Historial ordenado del periodo más antiguo al más reciente."""

    @abstractmethod
    def listar_por_periodo(self, periodo_id: int) -> List[Inscripcion]: ...

    @abstractmethod
    def guardar(self, inscripcion: Inscripcion) -> Inscripcion: ...
