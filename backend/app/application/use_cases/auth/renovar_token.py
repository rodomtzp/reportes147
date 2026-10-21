from app.application.ports.seguridad import TokenPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import NoAutenticado


class RenovarToken:
    def __init__(self, uow: UnidadDeTrabajo, tokens: TokenPuerto):
        self._uow = uow
        self._tokens = tokens

    def ejecutar(self, refresh_token: str) -> str:
        claims = self._tokens.decodificar(refresh_token)
        if claims.tipo != "refresh":
            raise NoAutenticado("Token inválido.")
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(claims.usuario_id)
        if usuario is None or not usuario.activo:
            raise NoAutenticado("Usuario no disponible.")
        if claims.version != usuario.sesion_version:
            raise NoAutenticado("La sesión ya no es válida. Inicia sesión de nuevo.")
        return self._tokens.emitir_access(usuario.id, sorted(r.value for r in usuario.roles), usuario.sesion_version)
