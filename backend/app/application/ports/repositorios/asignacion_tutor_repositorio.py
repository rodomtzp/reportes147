from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.asignacion_tutor import AsignacionTutor


class AsignacionTutorRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, asignacion_id: int) -> Optional[AsignacionTutor]: ...

    @abstractmethod
    def obtener_por_grupo_y_periodo(self, grupo_id: int, periodo_id: int) -> Optional[AsignacionTutor]: ...

    @abstractmethod
    def listar(
        self,
        periodo_id: Optional[int] = None,
        grupo_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
    ) -> List[AsignacionTutor]: ...

    @abstractmethod
    def guardar(self, asignacion: AsignacionTutor) -> AsignacionTutor: ...

    @abstractmethod
    def eliminar(self, asignacion_id: int) -> None: ...
