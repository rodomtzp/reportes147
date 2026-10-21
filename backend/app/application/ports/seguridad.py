from abc import ABC, abstractmethod
from dataclasses import dataclass


class HasherPuerto(ABC):
    @abstractmethod
    def hashear(self, password: str) -> str: ...

    @abstractmethod
    def verificar(self, password: str, password_hash: str) -> bool: ...


@dataclass(frozen=True)
class ClaimsToken:
    usuario_id: int
    tipo: str  # "access" | "refresh"
    version: int = 0  # versión de sesión del usuario al emitirse


class TokenPuerto(ABC):
    @abstractmethod
    def emitir_access(self, usuario_id: int, roles: list, version: int = 0) -> str: ...

    @abstractmethod
    def emitir_refresh(self, usuario_id: int, version: int = 0) -> str: ...

    @abstractmethod
    def decodificar(self, token: str) -> ClaimsToken:
        """Lanza NoAutenticado si el token es inválido o expiró."""
