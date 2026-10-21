from app.application.dto.auth import TokensDTO
from app.application.ports.seguridad import HasherPuerto, TokenPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_password import validar_password


class CambiarPassword:
    """Cierra las demás sesiones del usuario y devuelve tokens nuevos para la actual."""

    def __init__(self, uow: UnidadDeTrabajo, hasher: HasherPuerto, tokens: TokenPuerto):
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens

    def ejecutar(self, usuario_id: int, password_actual: str, password_nueva: str) -> TokensDTO:
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(usuario_id)
            if usuario is None:
                raise NoEncontrado("Usuario no encontrado.")
            if not self._hasher.verificar(password_actual, usuario.password_hash):
                raise ReglaDeNegocioViolada("La contraseña actual es incorrecta.")
            validar_password(password_nueva)
            if password_nueva == password_actual:
                raise ReglaDeNegocioViolada("La nueva contraseña debe ser distinta de la actual.")
            usuario.password_hash = self._hasher.hashear(password_nueva)
            usuario.debe_cambiar_password = False
            usuario.sesion_version += 1
            uow.usuarios.guardar(usuario)
            uow.commit()
            return TokensDTO(
                access_token=self._tokens.emitir_access(
                    usuario.id, sorted(r.value for r in usuario.roles), usuario.sesion_version),
                refresh_token=self._tokens.emitir_refresh(usuario.id, usuario.sesion_version),
            )
