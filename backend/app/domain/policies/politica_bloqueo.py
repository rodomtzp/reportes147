"""Bloqueo temporal de la cuenta tras varios intentos fallidos de inicio de sesión."""
from datetime import datetime, timedelta
from typing import Optional

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15


def minutos_restantes(bloqueado_hasta: Optional[datetime], ahora: datetime) -> int:
    """0 si la cuenta no está bloqueada; si lo está, minutos (redondeados hacia arriba) que faltan."""
    if bloqueado_hasta is None or bloqueado_hasta <= ahora:
        return 0
    return max(1, -(-int((bloqueado_hasta - ahora).total_seconds()) // 60))


def registrar_fallo(usuario, ahora: datetime) -> bool:
    """Suma un intento fallido; al llegar al máximo bloquea la cuenta. Devuelve True si quedó bloqueada."""
    usuario.intentos_fallidos += 1
    if usuario.intentos_fallidos >= MAX_INTENTOS:
        usuario.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
        usuario.intentos_fallidos = 0
        return True
    return False


def limpiar(usuario) -> bool:
    """Reinicia el contador. Devuelve True si había algo que limpiar."""
    hubo = usuario.intentos_fallidos > 0 or usuario.bloqueado_hasta is not None
    usuario.intentos_fallidos, usuario.bloqueado_hasta = 0, None
    return hubo
