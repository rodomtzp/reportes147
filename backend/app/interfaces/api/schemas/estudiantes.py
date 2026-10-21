from typing import List, Optional

from pydantic import Field

from app.domain.value_objects.estatus_estudiante import AccionAvance, EstatusEstudiante
from app.interfaces.api.schemas.base import EsquemaBase


class TutorLegalIn(EsquemaBase):
    nombre: str = Field(min_length=2, max_length=150)
    telefono: str = Field(min_length=7, max_length=20)
    parentesco: Optional[str] = Field(default=None, max_length=50)
    correo: Optional[str] = Field(default=None, max_length=254)
    es_principal: bool = False


class TutorLegalActualizarIn(EsquemaBase):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    telefono: Optional[str] = Field(default=None, min_length=7, max_length=20)
    parentesco: Optional[str] = Field(default=None, max_length=50)
    correo: Optional[str] = Field(default=None, max_length=254)
    es_principal: Optional[bool] = None


class EstudianteCrearIn(EsquemaBase):
    numero_control: str = Field(min_length=5, max_length=20)
    primer_apellido: str = Field(min_length=1, max_length=80)
    segundo_apellido: Optional[str] = Field(default=None, max_length=80)
    nombres: str = Field(min_length=1, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=20)
    correo: Optional[str] = Field(default=None, max_length=254)
    calle: Optional[str] = Field(default=None, max_length=120)
    numero: Optional[str] = Field(default=None, max_length=20)
    colonia: Optional[str] = Field(default=None, max_length=120)
    ciudad: Optional[str] = Field(default=None, max_length=120)
    generacion: str = Field(min_length=1, max_length=20)
    grupo_id: int = Field(gt=0)
    tutores: List[TutorLegalIn] = Field(min_length=1, max_length=5)


class EstudianteActualizarIn(EsquemaBase):
    primer_apellido: Optional[str] = Field(default=None, min_length=1, max_length=80)
    segundo_apellido: Optional[str] = Field(default=None, max_length=80)
    nombres: Optional[str] = Field(default=None, min_length=1, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=20)
    correo: Optional[str] = Field(default=None, max_length=254)
    calle: Optional[str] = Field(default=None, max_length=120)
    numero: Optional[str] = Field(default=None, max_length=20)
    colonia: Optional[str] = Field(default=None, max_length=120)
    ciudad: Optional[str] = Field(default=None, max_length=120)
    generacion: Optional[str] = Field(default=None, min_length=1, max_length=20)
    estatus: Optional[EstatusEstudiante] = None


class CambiarGrupoIn(EsquemaBase):
    grupo_id: int = Field(gt=0)


class ExcepcionAvanceIn(EsquemaBase):
    estudiante_id: int = Field(gt=0)
    accion: AccionAvance


class AvanceSemestreIn(EsquemaBase):
    periodo_origen_id: int = Field(gt=0)
    periodo_destino_id: int = Field(gt=0)
    excepciones: List[ExcepcionAvanceIn] = Field(default_factory=list, max_length=2000)
    simular: bool = True
