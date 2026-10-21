from app.application.ports.seguridad import TokenPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoAutenticado


class ObtenerUsuarioAutenticado:
    """Resuelve el usuario a partir de un access token.

    Se consulta la base en cada petición para que desactivar a un usuario
    o cambiarle los roles surta efecto de inmediato.
    """

    def __init__(self, uow: UnidadDeTrabajo, tokens: TokenPuerto):
        self._uow = uow
        self._tokens = tokens

    def ejecutar(self, access_token: str) -> Usuario:
        claims = self._tokens.decodificar(access_token)
        if claims.tipo != "access":
            raise NoAutenticado("Token inválido.")
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(claims.usuario_id)
        if usuario is None or not usuario.activo:
            raise NoAutenticado("Usuario no disponible.")
        if claims.version != usuario.sesion_version:
            raise NoAutenticado("La sesión ya no es válida. Inicia sesión de nuevo.")
        return usuario
