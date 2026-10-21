from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from app.domain.entities.estudiante import Estudiante
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante


class EstudianteRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, estudiante_id: int) -> Optional[Estudiante]: ...

    @abstractmethod
    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Estudiante]: ...

    @abstractmethod
    def obtener_por_numero_control(self, numero_control: str) -> Optional[Estudiante]: ...

    @abstractmethod
    def listar(
        self,
        texto: Optional[str] = None,
        estatus: Optional[EstatusEstudiante] = None,
        grupo_ids: Optional[List[int]] = None,
        carrera_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        limite: int = 200,
        offset: int = 0,
    ) -> List[Estudiante]:
        """Si se filtra por grupo_ids o carrera_id se usan las inscripciones de periodo_id."""

    @abstractmethod
    def buscar_activos(self, texto: str, limite: int = 15) -> List[Estudiante]: ...

    @abstractmethod
    def guardar(self, estudiante: Estudiante) -> Estudiante: ...
