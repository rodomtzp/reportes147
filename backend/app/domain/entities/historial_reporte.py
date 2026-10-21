from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects.estado_reporte import TipoEventoReporte


@dataclass
class HistorialReporte:
    """Bitácora inmutable: creación, cambios de estado y de gravedad, correcciones, cancelación y adjuntos."""

    reporte_id: int
    tipo: TipoEventoReporte
    usuario_id: int
    fecha: datetime
    campo: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    comentario: Optional[str] = None
    id: Optional[int] = None
