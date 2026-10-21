from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from app.domain.entities.usuario import Usuario
from app.domain.value_objects.rol import Rol


class UsuarioRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]: ...

    @abstractmethod
    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Usuario]: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def listar(self, rol: Optional[Rol] = None, activo: Optional[bool] = None) -> List[Usuario]: ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...
