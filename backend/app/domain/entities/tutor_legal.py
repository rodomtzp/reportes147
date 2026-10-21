from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_contacto import limpiar, normalizar_correo, normalizar_telefono


@dataclass
class TutorLegal:
    """Padre, madre o tutor legal a quien se llama cuando se reporta al estudiante."""

    nombre: str
    telefono: str
    estudiante_id: Optional[int] = None
    parentesco: Optional[str] = None
    correo: Optional[str] = None
    es_principal: bool = False
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.nombre = limpiar(self.nombre) or ""
        if not self.nombre:
            raise ReglaDeNegocioViolada("El nombre del padre o tutor es obligatorio.")
        self.telefono = normalizar_telefono(self.telefono)
        self.parentesco = limpiar(self.parentesco)
        self.correo = normalizar_correo(self.correo)
