from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects.accion_bitacora import AccionBitacora


@dataclass
class RegistroBitacora:
    """Quién accedió a datos sensibles (contacto) o exportó información, y cuándo. Solo se agrega."""

    accion: AccionBitacora
    usuario_id: int
    fecha: datetime
    descripcion: str
    estudiante_id: Optional[int] = None
    grupo_id: Optional[int] = None
    carrera_id: Optional[int] = None
    filas: Optional[int] = None
    con_contacto: bool = False
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.accion = AccionBitacora(self.accion)
        self.descripcion = (self.descripcion or "").strip()[:300]
