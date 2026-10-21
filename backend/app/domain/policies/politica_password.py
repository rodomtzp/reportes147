import secrets

from app.domain.exceptions import ReglaDeNegocioViolada

LONGITUD_MINIMA = 10


def validar_password(password: str) -> None:
    if len(password or "") < LONGITUD_MINIMA:
        raise ReglaDeNegocioViolada(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres."
        )


def generar_password_temporal() -> str:
    """12 caracteres aleatorios y seguros (URL-safe)."""
    return secrets.token_urlsafe(9)
