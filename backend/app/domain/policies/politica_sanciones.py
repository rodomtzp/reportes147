from typing import Optional

from app.domain.entities.sancion import DIAS_MAX, DIAS_MIN
from app.domain.entities.tipo_sancion import TipoSancion
from app.domain.exceptions import ReglaDeNegocioViolada


def validar_tipo_y_dias(tipo: TipoSancion, dias: Optional[int]) -> Optional[int]:
    """La sanción debe usar un tipo activo; los días son obligatorios solo si el tipo los requiere."""
    if not tipo.activo:
        raise ReglaDeNegocioViolada("Ese tipo de sanción está desactivado.")
    if tipo.requiere_dias:
        if dias is None:
            raise ReglaDeNegocioViolada(f"'{tipo.nombre}' requiere indicar el número de días.")
        if not DIAS_MIN <= dias <= DIAS_MAX:
            raise ReglaDeNegocioViolada(f"Los días deben estar entre {DIAS_MIN} y {DIAS_MAX}.")
        return dias
    return None
