from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada

SEMESTRE_MIN = 1
SEMESTRE_MAX = 6


@dataclass
class Grupo:
    """Un grupo se identifica por semestre + letra (1G, 2G...).

    La letra se conserva al avanzar de semestre: 1G → 2G → 3G.
    Un grupo pertenece a una sola carrera; una carrera tiene varios grupos.
    """

    carrera_id: int
    semestre: int
    letra: str
    activo: bool = True
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.letra = self.letra.strip().upper()
        if len(self.letra) != 1 or not self.letra.isalpha():
            raise ReglaDeNegocioViolada("La letra del grupo debe ser un solo carácter alfabético.")
        if not SEMESTRE_MIN <= self.semestre <= SEMESTRE_MAX:
            raise ReglaDeNegocioViolada(
                f"El semestre debe estar entre {SEMESTRE_MIN} y {SEMESTRE_MAX}."
            )

    @property
    def clave(self) -> str:
        return f"{self.semestre}{self.letra}"

    def clave_siguiente(self) -> Optional[str]:
        """Clave del grupo al que pasan sus estudiantes (None si es el último semestre)."""
        if self.semestre >= SEMESTRE_MAX:
            return None
        return f"{self.semestre + 1}{self.letra}"
