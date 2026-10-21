from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.tipo_sancion import TipoSancion


class TipoSancionRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, tipo_id: int) -> Optional[TipoSancion]: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Optional[TipoSancion]: ...

    @abstractmethod
    def listar(self, solo_activos: bool = False) -> List[TipoSancion]: ...

    @abstractmethod
    def guardar(self, tipo: TipoSancion) -> TipoSancion: ...
