from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.mensaje_whatsapp import MensajeWhatsApp


class MensajeWhatsAppRepositorio(ABC):
    @abstractmethod
    def guardar(self, mensaje: MensajeWhatsApp) -> MensajeWhatsApp: ...

    @abstractmethod
    def obtener_por_id(self, mensaje_id: int) -> Optional[MensajeWhatsApp]: ...

    @abstractmethod
    def listar_por_reporte(self, reporte_id: int) -> List[MensajeWhatsApp]: ...

    @abstractmethod
    def tutor_tiene_mensajes(self, tutor_id: int) -> bool: ...
