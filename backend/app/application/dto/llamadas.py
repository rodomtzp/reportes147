from dataclasses import dataclass
from typing import List, Optional

from app.domain.entities.intento_llamada import IntentoLlamada
from app.domain.entities.mensaje_whatsapp import MensajeWhatsApp
from app.domain.entities.tutor_legal import TutorLegal


@dataclass(frozen=True)
class LlamadaDetalle:
    intento: IntentoLlamada
    tutor_nombre: str
    tutor_parentesco: Optional[str]
    realizado_por_nombre: Optional[str]


@dataclass(frozen=True)
class MensajeDetalle:
    mensaje: MensajeWhatsApp
    tutor_nombre: str
    generado_por_nombre: str


@dataclass(frozen=True)
class SeguimientoLlamadas:
    """Vista de Orientación: incluye teléfonos."""

    folio: str
    estudiante: str
    estado_llamada: str
    tutores: List[TutorLegal]
    llamadas: List[LlamadaDetalle]
    mensajes: List[MensajeDetalle]


@dataclass(frozen=True)
class MensajeGenerado:
    mensaje: MensajeWhatsApp
    tutor: TutorLegal
    enlace: str
