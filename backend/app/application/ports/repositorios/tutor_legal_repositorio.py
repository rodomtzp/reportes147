from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.tutor_legal import TutorLegal


class TutorLegalRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, tutor_id: int) -> Optional[TutorLegal]: ...

    @abstractmethod
    def listar_por_estudiante(self, estudiante_id: int) -> List[TutorLegal]: ...

    @abstractmethod
    def guardar(self, tutor: TutorLegal) -> TutorLegal: ...

    @abstractmethod
    def eliminar(self, tutor_id: int) -> None: ...
