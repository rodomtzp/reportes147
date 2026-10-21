from typing import Optional

from pydantic import Field

from app.interfaces.api.schemas.base import EsquemaBase


class TipoIncidenciaCrearIn(EsquemaBase):
    nombre: str = Field(min_length=2, max_length=100)


class TipoIncidenciaActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    activo: Optional[bool] = None


class TipoSancionCrearIn(EsquemaBase):
    nombre: str = Field(min_length=2, max_length=100)
    requiere_dias: bool = False


class TipoSancionActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    requiere_dias: Optional[bool] = None
    activo: Optional[bool] = None
