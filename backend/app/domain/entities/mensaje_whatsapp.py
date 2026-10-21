from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MensajeWhatsApp:
    """Registro del mensaje generado para un padre o tutor (el envío es manual por ahora)."""

    reporte_id: int
    tutor_legal_id: int
    texto: str
    generado_por: int
    generado_en: datetime
    enviado_en: Optional[datetime] = None  # cuando el usuario confirma que lo envió
    id: Optional[int] = None
