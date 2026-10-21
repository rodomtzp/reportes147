from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.domain.value_objects.estado_llamada import EstadoLlamada
from app.domain.value_objects.gravedad import Gravedad
from app.interfaces.api.schemas.base import EsquemaBase


class ReporteCrearIn(EsquemaBase):
    estudiante_ids: List[int] = Field(min_length=1, max_length=20)
    tipo_incidencia_id: int = Field(gt=0)
    descripcion: str = Field(min_length=10, max_length=2000)
    gravedad: Gravedad
    descripcion_otro: Optional[str] = Field(default=None, max_length=200)
    fecha_hora_incidente: Optional[datetime] = None


class ReporteCorregirIn(EsquemaBase):
    tipo_incidencia_id: Optional[int] = Field(default=None, gt=0)
    descripcion_otro: Optional[str] = Field(default=None, max_length=200)
    descripcion: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    fecha_hora_incidente: Optional[datetime] = None
    comentario: Optional[str] = Field(default=None, max_length=500)


class CambiarGravedadIn(EsquemaBase):
    gravedad: Gravedad
    motivo: str = Field(min_length=5, max_length=500)


class TurnarIn(EsquemaBase):
    comentario: Optional[str] = Field(default=None, max_length=500)


class CancelarIn(EsquemaBase):
    motivo: str = Field(min_length=10, max_length=500)


class LlamadaIn(EsquemaBase):
    estado: EstadoLlamada
    tutor_legal_id: Optional[int] = Field(default=None, gt=0)
    atendio_nombre: Optional[str] = Field(default=None, max_length=120)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    fecha_hora: Optional[datetime] = None


class MensajeWhatsAppIn(EsquemaBase):
    tutor_legal_id: Optional[int] = Field(default=None, gt=0)
