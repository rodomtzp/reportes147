from typing import Optional

from pydantic import Field

from app.interfaces.api.schemas.base import EsquemaBase


class SancionIn(EsquemaBase):
    tipo_sancion_id: int = Field(gt=0)
    dias: Optional[int] = Field(default=None, ge=1, le=365)
    observaciones: Optional[str] = Field(default=None, max_length=1000)
