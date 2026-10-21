from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Type, TypeVar

from flask import current_app, request
from pydantic import BaseModel

from app.domain.exceptions import ReglaDeNegocioViolada

T = TypeVar("T", bound=BaseModel)


def contenedor():
    return current_app.extensions["container"]


def leer(esquema: Type[T]) -> T:
    """Valida el cuerpo JSON; los errores salen como 422 (ver errors.py)."""
    return esquema.model_validate(request.get_json(silent=True) or {})


def parametros_cambiados(modelo: BaseModel) -> dict:
    """Solo los campos que el cliente envió (para PATCH parciales)."""
    return modelo.model_dump(exclude_unset=True)


def arg_bool(nombre: str):
    valor = request.args.get(nombre)
    if valor is None:
        return None
    return valor.lower() in ("1", "true", "si", "sí")


def arg_enum(nombre: str, enum_cls: Type[Enum]):
    valor = request.args.get(nombre)
    if not valor:
        return None
    try:
        return enum_cls(valor)
    except ValueError:
        validos = ", ".join(e.value for e in enum_cls)
        raise ReglaDeNegocioViolada(f"'{nombre}' inválido. Valores permitidos: {validos}.")


def arg_fecha(nombre: str, fin_de_dia: bool = False) -> Optional[datetime]:
    """Acepta AAAA-MM-DD o AAAA-MM-DDTHH:MM; sin zona se interpreta en la zona local."""
    valor = request.args.get(nombre)
    if not valor:
        return None
    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError:
        raise ReglaDeNegocioViolada(f"'{nombre}' debe tener formato AAAA-MM-DD o AAAA-MM-DDTHH:MM.")
    if fin_de_dia and len(valor) == 10:
        fecha = fecha + timedelta(days=1) - timedelta(seconds=1)
    return contenedor().reloj.localizar(fecha)
