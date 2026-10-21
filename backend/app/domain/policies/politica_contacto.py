import re
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_telefono(valor: str) -> str:
    """Devuelve 10 dígitos (México). Acepta espacios, guiones, paréntesis y lada +52 / +521."""
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 13 and digitos.startswith("521"):
        digitos = digitos[3:]
    elif len(digitos) == 12 and digitos.startswith("52"):
        digitos = digitos[2:]
    if len(digitos) != 10:
        raise ReglaDeNegocioViolada("El teléfono debe tener 10 dígitos.")
    return digitos


def normalizar_correo(valor: Optional[str]) -> Optional[str]:
    if valor is None or not valor.strip():
        return None
    correo = valor.strip().lower()
    if not _EMAIL.match(correo):
        raise ReglaDeNegocioViolada("El correo electrónico no es válido.")
    return correo


def limpiar(valor: Optional[str]) -> Optional[str]:
    """Recorta y colapsa espacios; devuelve None si queda vacío."""
    if valor is None:
        return None
    texto = " ".join(str(valor).split())
    return texto or None
