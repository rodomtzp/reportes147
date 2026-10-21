import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import List

from app.application.ports.correo import CorreoPuerto

log = logging.getLogger(__name__)


class CorreoNulo(CorreoPuerto):
    """Se usa cuando no hay servidor SMTP configurado: la alerta queda en la bandeja y se registra el motivo."""

    def enviar(self, destinatarios: List[str], asunto: str, cuerpo: str) -> None:
        log.warning("Correo no enviado (SMTP no configurado): %s → %s", asunto, ", ".join(destinatarios))
        raise RuntimeError("SMTP no configurado")


class CorreoSMTP(CorreoPuerto):
    def __init__(self, host: str, puerto: int, usuario: str, password: str, remitente: str,
                 starttls: bool = True, timeout: int = 8):
        self._host, self._puerto, self._usuario, self._password = host, puerto, usuario, password
        self._remitente, self._starttls, self._timeout = remitente or usuario, starttls, timeout

    def enviar(self, destinatarios: List[str], asunto: str, cuerpo: str) -> None:
        mensaje = EmailMessage()
        mensaje["Subject"], mensaje["From"], mensaje["To"] = asunto, self._remitente, ", ".join(destinatarios)
        mensaje.set_content(cuerpo)
        contexto = ssl.create_default_context()
        if self._puerto == 465:
            servidor = smtplib.SMTP_SSL(self._host, self._puerto, timeout=self._timeout, context=contexto)
        else:
            servidor = smtplib.SMTP(self._host, self._puerto, timeout=self._timeout)
        with servidor as s:
            if self._puerto != 465 and self._starttls:
                s.starttls(context=contexto)
            if self._usuario:
                s.login(self._usuario, self._password)
            s.send_message(mensaje)
