from urllib.parse import quote

from app.application.ports.mensajeria import MensajePreparado, MensajeriaPuerto


class MensajeriaEnlaceManual(MensajeriaPuerto):
    """El usuario abre el enlace y envía el mensaje desde su propio WhatsApp.

    Sustituible por una implementación con la API de WhatsApp Business (envío directo)."""

    def __init__(self, codigo_pais: str = "52"):
        self._codigo = "".join(c for c in codigo_pais if c.isdigit())

    def preparar(self, telefono: str, texto: str) -> MensajePreparado:
        return MensajePreparado(enlace=f"https://wa.me/{self._codigo}{telefono}?text={quote(texto)}")
