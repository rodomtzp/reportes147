from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Notificacion:
    """Alerta en la bandeja compartida de un rol (hoy, Subdirección)."""

    tipo: str  # REPORTE_GRAVE | ACUMULACION
    titulo: str
    mensaje: str
    rol_destino: str
    creada_en: datetime
    reporte_id: Optional[int] = None
    estudiante_id: Optional[int] = None
    correo_enviado: bool = False
    correo_error: Optional[str] = None
    atendida_por: Optional[int] = None
    atendida_en: Optional[datetime] = None
    id: Optional[int] = None
