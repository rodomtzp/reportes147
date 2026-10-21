from typing import Iterable

from app.application.ports.seguridad import HasherPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import Conflicto, ReglaDeNegocioViolada
from app.domain.policies.politica_password import validar_password
from app.domain.value_objects.rol import Rol


class CrearUsuario:
    def __init__(self, uow: UnidadDeTrabajo, hasher: HasherPuerto):
        self._uow = uow
        self._hasher = hasher

    def ejecutar(
        self,
        nombre: str,
        correo: str,
        password: str,
        roles: Iterable,
        debe_cambiar_password: bool = False,
    ) -> Usuario:
        if not nombre.strip():
            raise ReglaDeNegocioViolada("El nombre es obligatorio.")
        roles = frozenset(Rol(r) for r in roles)
        if not roles:
            raise ReglaDeNegocioViolada("El usuario debe tener al menos un rol.")
        validar_password(password)
        with self._uow as uow:
            if uow.usuarios.obtener_por_correo(correo.strip().lower()):
                raise Conflicto("Ya existe un usuario con ese correo.")
            usuario = Usuario(
                nombre=nombre.strip(),
                correo=correo,
                password_hash=self._hasher.hashear(password),
                roles=roles,
                debe_cambiar_password=debe_cambiar_password,
            )
            uow.usuarios.guardar(usuario)
            uow.commit()
            return usuario
