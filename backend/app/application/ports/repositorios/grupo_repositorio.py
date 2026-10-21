from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.grupo import Grupo


class GrupoRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, grupo_id: int) -> Optional[Grupo]: ...

    @abstractmethod
    def obtener_por_semestre_y_letra(self, semestre: int, letra: str) -> Optional[Grupo]: ...

    @abstractmethod
    def listar(
        self,
        carrera_id: Optional[int] = None,
        semestre: Optional[int] = None,
        solo_activos: bool = False,
    ) -> List[Grupo]: ...

    @abstractmethod
    def guardar(self, grupo: Grupo) -> Grupo: ...
