from typing import List, Optional

from pydantic import Field

from app.domain.value_objects.rol import Rol
from app.interfaces.api.schemas.base import EMAIL_PATTERN, EsquemaBase


class UsuarioCrearIn(EsquemaBase):
    nombre: str = Field(min_length=2, max_length=150)
    correo: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    roles: List[Rol] = Field(min_length=1)


class UsuarioActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    roles: Optional[List[Rol]] = Field(default=None, min_length=1)
    activo: Optional[bool] = None
