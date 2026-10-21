from abc import ABC, abstractmethod


class AlmacenArchivosPuerto(ABC):
    @abstractmethod
    def guardar(self, contenido: bytes, extension: str) -> str:
        """Guarda el archivo y devuelve una clave opaca para recuperarlo."""

    @abstractmethod
    def leer(self, clave: str) -> bytes: ...
