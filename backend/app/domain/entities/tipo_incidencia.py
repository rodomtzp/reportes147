from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada


@dataclass
class TipoIncidencia:
    nombre: str
    activo: bool = True
    es_otro: bool = False  # opción "Otro": permite descripción libre en el reporte
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.nombre = self.nombre.strip()
        if not self.nombre:
            raise ReglaDeNegocioViolada("El tipo de incidencia requiere un nombre.")
