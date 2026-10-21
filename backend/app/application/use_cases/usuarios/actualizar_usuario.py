from typing import Iterable, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.rol import Rol


class ActualizarUsuario:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        actor_id: int,
        usuario_id: int,
        nombre: Optional[str] = None,
        roles: Optional[Iterable] = None,
        activo: Optional[bool] = None,
    ) -> Usuario:
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(usuario_id)
            if usuario is None:
                raise NoEncontrado("Usuario no encontrado.")

            nuevos_roles = frozenset(Rol(r) for r in roles) if roles is not None else None
            if actor_id == usuario_id:  # evita que el administrador se bloquee a sí mismo
                if activo is False:
                    raise ReglaDeNegocioViolada("No puedes desactivar tu propia cuenta.")
                if (
                    nuevos_roles is not None
                    and Rol.ADMINISTRADOR in usuario.roles
                    and Rol.ADMINISTRADOR not in nuevos_roles
                ):
                    raise ReglaDeNegocioViolada("No puedes quitarte el rol de Administrador.")

            if nombre is not None:
                if not nombre.strip():
                    raise ReglaDeNegocioViolada("El nombre es obligatorio.")
                usuario.nombre = nombre.strip()

            if nuevos_roles is not None:
                if not nuevos_roles:
                    raise ReglaDeNegocioViolada("El usuario debe tener al menos un rol.")
                if Rol.DOCENTE in usuario.roles and Rol.DOCENTE not in nuevos_roles:
                    vigente = uow.periodos.obtener_vigente()
                    if vigente and uow.asignaciones_tutor.listar(
                        periodo_id=vigente.id, usuario_id=usuario_id
                    ):
                        raise ReglaDeNegocioViolada(
                            "El usuario es tutor en el periodo vigente. Retira primero sus asignaciones."
                        )
                usuario.roles = nuevos_roles

            if activo is not None:
                if usuario.activo and not activo:
                    usuario.sesion_version += 1              # al reactivarla no revive sesiones viejas
                usuario.activo = activo

            uow.usuarios.guardar(usuario)
            uow.commit()
            return usuario
