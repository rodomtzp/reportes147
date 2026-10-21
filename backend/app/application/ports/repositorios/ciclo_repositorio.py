from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.ciclo_acumulacion import CicloAcumulacion


class CicloRepositorio(ABC):
    @abstractmethod
    def obtener_abierto(self, estudiante_id: int) -> Optional[CicloAcumulacion]: ...

    @abstractmethod
    def listar_por_estudiante(self, estudiante_id: int) -> List[CicloAcumulacion]: ...

    @abstractmethod
    def siguiente_numero(self, estudiante_id: int) -> int: ...

    @abstractmethod
    def guardar(self, ciclo: CicloAcumulacion) -> CicloAcumulacion: ...
