from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.notificacion import Notificacion


class NotificacionRepositorio(ABC):
    @abstractmethod
    def guardar(self, notificacion: Notificacion) -> Notificacion: ...

    @abstractmethod
    def obtener_por_id(self, notificacion_id: int) -> Optional[Notificacion]: ...

    @abstractmethod
    def listar(self, rol_destino: str, solo_pendientes: bool = False, limite: int = 100, offset: int = 0) -> List[Notificacion]: ...

    @abstractmethod
    def contar_pendientes(self, rol_destino: str) -> int: ...
