from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.carrera import Carrera


class CarreraRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, carrera_id: int) -> Optional[Carrera]: ...

    @abstractmethod
    def obtener_por_clave(self, clave: str) -> Optional[Carrera]: ...

    @abstractmethod
    def listar(self, solo_activas: bool = False) -> List[Carrera]: ...

    @abstractmethod
    def guardar(self, carrera: Carrera) -> Carrera: ...
