from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada


@dataclass
class TipoSancion:
    nombre: str
    requiere_dias: bool = False  # p. ej. "Suspensión de N días"
    activo: bool = True
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.nombre = self.nombre.strip()
        if not self.nombre:
            raise ReglaDeNegocioViolada("El tipo de sanción requiere un nombre.")
