from abc import ABC, abstractmethod
from typing import List


class CorreoPuerto(ABC):
    @abstractmethod
    def enviar(self, destinatarios: List[str], asunto: str, cuerpo: str) -> None:
        """Lanza una excepción si no se pudo enviar."""
