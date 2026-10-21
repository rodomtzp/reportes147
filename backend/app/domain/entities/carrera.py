from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada


@dataclass
class Carrera:
    nombre: str
    clave: str
    activa: bool = True
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.nombre = self.nombre.strip()
        self.clave = self.clave.strip().upper()
        if not self.nombre or not self.clave:
            raise ReglaDeNegocioViolada("La carrera requiere nombre y clave.")
