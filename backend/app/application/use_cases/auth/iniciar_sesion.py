from app.application.dto.auth import TokensDTO
from app.application.ports.reloj import RelojPuerto
from app.application.ports.seguridad import HasherPuerto, TokenPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import CredencialesInvalidas, CuentaBloqueada
from app.domain.policies.politica_bloqueo import limpiar, minutos_restantes, registrar_fallo

# Contraseña señuelo para igualar el tiempo de respuesta cuando el correo no existe.
_PASSWORD_SENUELO = "senuelo-no-es-una-contrasena-real"


def _mensaje_bloqueo(minutos: int) -> str:
    return f"Demasiados intentos fallidos. Intenta de nuevo en {minutos} minuto{'s' if minutos != 1 else ''}."


class IniciarSesion:
    """Tras 5 intentos fallidos la cuenta se bloquea 15 minutos (el administrador puede restablecerla)."""

    def __init__(self, uow: UnidadDeTrabajo, hasher: HasherPuerto, tokens: TokenPuerto, reloj: RelojPuerto):
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens
        self._reloj = reloj
        self._hash_senuelo = hasher.hashear(_PASSWORD_SENUELO)

    def ejecutar(self, correo: str, password: str) -> TokensDTO:
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_correo((correo or "").strip().lower())
            ahora = self._reloj.ahora()
            if usuario is not None and usuario.bloqueado_hasta is not None:
                usuario.bloqueado_hasta = self._reloj.localizar(usuario.bloqueado_hasta)
                faltan = minutos_restantes(usuario.bloqueado_hasta, ahora)
                if faltan:
                    raise CuentaBloqueada(_mensaje_bloqueo(faltan))

            hash_a_verificar = usuario.password_hash if usuario else self._hash_senuelo
            password_ok = self._hasher.verificar(password or "", hash_a_verificar)

            if usuario is None or not usuario.activo:
                raise CredencialesInvalidas("Correo o contraseña incorrectos.")
            if not password_ok:
                bloqueada = registrar_fallo(usuario, ahora)
                uow.usuarios.guardar(usuario)
                uow.commit()
                if bloqueada:
                    raise CuentaBloqueada(_mensaje_bloqueo(minutos_restantes(usuario.bloqueado_hasta, ahora)))
                raise CredencialesInvalidas("Correo o contraseña incorrectos.")
            if limpiar(usuario):
                uow.usuarios.guardar(usuario)
                uow.commit()

        return TokensDTO(
            access_token=self._tokens.emitir_access(
                usuario.id, sorted(r.value for r in usuario.roles), usuario.sesion_version
            ),
            refresh_token=self._tokens.emitir_refresh(usuario.id, usuario.sesion_version),
        )
