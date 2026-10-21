from app.application.ports.seguridad import HasherPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import NoEncontrado
from app.domain.policies.politica_password import generar_password_temporal


class RestablecerPassword:
    """El administrador genera una nueva contraseña temporal; el usuario deberá cambiarla."""

    def __init__(self, uow: UnidadDeTrabajo, hasher: HasherPuerto):
        self._uow = uow
        self._hasher = hasher

    def ejecutar(self, usuario_id: int) -> str:
        temporal = generar_password_temporal()
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(usuario_id)
            if usuario is None:
                raise NoEncontrado("Usuario no encontrado.")
            usuario.password_hash = self._hasher.hashear(temporal)
            usuario.debe_cambiar_password = True
            usuario.sesion_version += 1                      # cierra las sesiones abiertas
            usuario.intentos_fallidos, usuario.bloqueado_hasta = 0, None   # y desbloquea la cuenta
            uow.usuarios.guardar(usuario)
            uow.commit()
        return temporal
