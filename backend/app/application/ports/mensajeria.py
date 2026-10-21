from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MensajePreparado:
    enlace: str
    enviado_automaticamente: bool = False  # True cuando exista la integración con la API de WhatsApp


class MensajeriaPuerto(ABC):
    @abstractmethod
    def preparar(self, telefono: str, texto: str) -> MensajePreparado:
        """`telefono`: 10 dígitos. Hoy devuelve un enlace para enviarlo manualmente; una implementación
        con WhatsApp Business API podrá enviarlo directamente sin cambiar los casos de uso."""
