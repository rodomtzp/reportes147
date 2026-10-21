from datetime import date
from typing import Optional

from pydantic import Field, model_validator

from app.interfaces.api.schemas.base import EsquemaBase


class CarreraCrearIn(EsquemaBase):
    nombre: str = Field(min_length=2, max_length=150)
    clave: str = Field(min_length=1, max_length=20)


class CarreraActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    clave: Optional[str] = Field(default=None, min_length=1, max_length=20)
    activa: Optional[bool] = None


class GrupoCrearIn(EsquemaBase):
    carrera_id: int = Field(gt=0)
    semestre: int = Field(ge=1, le=6)
    letra: str = Field(min_length=1, max_length=1)


class GrupoActualizarIn(EsquemaBase):
    carrera_id: Optional[int] = Field(default=None, gt=0)
    semestre: Optional[int] = Field(default=None, ge=1, le=6)
    letra: Optional[str] = Field(default=None, min_length=1, max_length=1)
    activo: Optional[bool] = None


class PeriodoCrearIn(EsquemaBase):
    nombre: str = Field(min_length=1, max_length=30)
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def _fechas(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio.")
        return self


class PeriodoActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=30)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class AsignacionTutorCrearIn(EsquemaBase):
    usuario_id: int = Field(gt=0)
    grupo_id: int = Field(gt=0)
    periodo_id: int = Field(gt=0)
