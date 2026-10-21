from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.adjunto import Adjunto


class AdjuntoRepositorio(ABC):
    @abstractmethod
    def guardar(self, adjunto: Adjunto) -> Adjunto: ...

    @abstractmethod
    def obtener_por_id(self, adjunto_id: int) -> Optional[Adjunto]: ...

    @abstractmethod
    def listar_por_reporte(self, reporte_id: int) -> List[Adjunto]: ...
