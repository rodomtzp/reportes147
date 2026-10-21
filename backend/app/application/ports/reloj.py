from abc import ABC, abstractmethod
from datetime import datetime


class RelojPuerto(ABC):
    @abstractmethod
    def ahora(self) -> datetime:
        """Hora actual con zona horaria local."""

    @abstractmethod
    def localizar(self, valor: datetime) -> datetime:
        """Asigna la zona local a una fecha sin zona; convierte a la local si ya la tiene."""
