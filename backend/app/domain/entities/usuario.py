from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.value_objects.rol import Rol


@dataclass
class Usuario:
    nombre: str
    correo: str
    password_hash: str
    activo: bool = True
    debe_cambiar_password: bool = False
    roles: frozenset = field(default_factory=frozenset)
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    sesion_version: int = 0  # al subirla, los tokens emitidos antes dejan de servir
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.correo = self.correo.strip().lower()
        self.roles = frozenset(Rol(r) for r in self.roles)

    def tiene_rol(self, rol: Rol) -> bool:
        return rol in self.roles
