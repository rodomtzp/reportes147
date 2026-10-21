from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada


@dataclass
class PeriodoEscolar:
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    vigente: bool = False
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.nombre = self.nombre.strip()
        if not self.nombre:
            raise ReglaDeNegocioViolada("El periodo requiere un nombre.")
        if self.fecha_fin <= self.fecha_inicio:
            raise ReglaDeNegocioViolada("La fecha de fin debe ser posterior a la de inicio.")
