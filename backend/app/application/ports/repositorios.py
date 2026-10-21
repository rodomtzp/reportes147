from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.usuario import Usuario


class UsuarioRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...
