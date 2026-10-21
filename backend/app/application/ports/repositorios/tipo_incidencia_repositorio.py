from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.tipo_incidencia import TipoIncidencia


class TipoIncidenciaRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, tipo_id: int) -> Optional[TipoIncidencia]: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Optional[TipoIncidencia]: ...

    @abstractmethod
    def listar(self, solo_activos: bool = False) -> List[TipoIncidencia]: ...

    @abstractmethod
    def guardar(self, tipo: TipoIncidencia) -> TipoIncidencia: ...
