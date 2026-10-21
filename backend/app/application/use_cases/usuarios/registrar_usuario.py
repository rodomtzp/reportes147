from typing import Iterable, Tuple

from app.application.ports.seguridad import HasherPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.usuarios.crear_usuario import CrearUsuario
from app.domain.entities.usuario import Usuario
from app.domain.policies.politica_password import generar_password_temporal


class RegistrarUsuario:
    """Alta hecha por un administrador: genera una contraseña temporal de un solo uso."""

    def __init__(self, uow: UnidadDeTrabajo, hasher: HasherPuerto):
        self._crear = CrearUsuario(uow, hasher)

    def ejecutar(self, nombre: str, correo: str, roles: Iterable) -> Tuple[Usuario, str]:
        temporal = generar_password_temporal()
        usuario = self._crear.ejecutar(nombre, correo, temporal, roles, debe_cambiar_password=True)
        return usuario, temporal
