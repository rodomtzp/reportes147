import pytest

from app.application.use_cases.auth.cambiar_password import CambiarPassword
from app.application.use_cases.auth.iniciar_sesion import IniciarSesion
from app.application.use_cases.auth.obtener_usuario_autenticado import ObtenerUsuarioAutenticado
from app.application.use_cases.auth.renovar_token import RenovarToken
from app.domain.exceptions import CredencialesInvalidas, NoAutenticado, ReglaDeNegocioViolada
from app.infrastructure.security.token_jwt import TokenJWT
from tests.unit.conftest import PASSWORD


def test_login_correcto_devuelve_tokens(uow, hasher, tokens, crear_usuario, reloj):
    crear_usuario("ana@cbtis.mx")
    res = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ANA@cbtis.mx", PASSWORD)
    assert res.access_token and res.refresh_token


@pytest.mark.parametrize("correo,password", [("ana@cbtis.mx", "mala"), ("nadie@cbtis.mx", PASSWORD)])
def test_login_incorrecto_usa_mensaje_generico(uow, hasher, tokens, crear_usuario, correo, password, reloj):
    crear_usuario("ana@cbtis.mx")
    with pytest.raises(CredencialesInvalidas):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar(correo, password)


def test_usuario_inactivo_no_inicia_sesion(uow, hasher, tokens, crear_usuario, reloj):
    u = crear_usuario("ana@cbtis.mx")
    u.activo = False
    uow.usuarios.guardar(u)
    with pytest.raises(CredencialesInvalidas):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)


def test_access_resuelve_usuario_y_refresh_no_sirve_como_access(uow, hasher, tokens, crear_usuario, reloj):
    u = crear_usuario("ana@cbtis.mx")
    res = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    resolver = ObtenerUsuarioAutenticado(uow, tokens)
    assert resolver.ejecutar(res.access_token).id == u.id
    with pytest.raises(NoAutenticado):
        resolver.ejecutar(res.refresh_token)


def test_refresh_emite_nuevo_access_y_access_no_sirve_como_refresh(uow, hasher, tokens, crear_usuario, reloj):
    crear_usuario("ana@cbtis.mx")
    res = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    renovar = RenovarToken(uow, tokens)
    assert renovar.ejecutar(res.refresh_token)
    with pytest.raises(NoAutenticado):
        renovar.ejecutar(res.access_token)


def test_token_alterado_expirado_o_de_otra_clave_es_rechazado(tokens):
    with pytest.raises(NoAutenticado):
        tokens.decodificar("basura")
    with pytest.raises(NoAutenticado):
        tokens.decodificar(TokenJWT("x" * 40, -1, 8).emitir_access(1, []))
    with pytest.raises(NoAutenticado):
        tokens.decodificar(TokenJWT("y" * 40, 15, 8).emitir_access(1, []))


def test_cambiar_password_limpia_la_marca_de_cambio_pendiente(uow, hasher, crear_usuario, tokens):
    u = crear_usuario("ana@cbtis.mx", debe_cambiar_password=True)
    assert u.debe_cambiar_password
    CambiarPassword(uow, hasher, tokens).ejecutar(u.id, PASSWORD, "otra-clave-larga-456")
    actualizado = uow.usuarios.obtener_por_id(u.id)
    assert not actualizado.debe_cambiar_password
    assert hasher.verificar("otra-clave-larga-456", actualizado.password_hash)


@pytest.mark.parametrize("actual,nueva", [("incorrecta", "otra-clave-larga-456"), (PASSWORD, "corta"), (PASSWORD, PASSWORD)])
def test_cambiar_password_rechaza_casos_invalidos(uow, hasher, crear_usuario, actual, nueva, tokens):
    u = crear_usuario("ana@cbtis.mx")
    with pytest.raises(ReglaDeNegocioViolada):
        CambiarPassword(uow, hasher, tokens).ejecutar(u.id, actual, nueva)


# ---------- bloqueo por intentos fallidos y cierre de sesiones ----------
def _fallar(uow, hasher, tokens, reloj, veces, correo="ana@cbtis.mx"):
    for _ in range(veces):
        with pytest.raises(CredencialesInvalidas):
            IniciarSesion(uow, hasher, tokens, reloj).ejecutar(correo, "mala-contrasena")


def test_el_quinto_intento_fallido_bloquea_la_cuenta_y_ni_la_clave_correcta_entra(uow, hasher, tokens, crear_usuario, reloj):
    from app.domain.exceptions import CuentaBloqueada

    crear_usuario("ana@cbtis.mx")
    _fallar(uow, hasher, tokens, reloj, 4)
    with pytest.raises(CuentaBloqueada, match="15 minutos"):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", "mala-contrasena")
    with pytest.raises(CuentaBloqueada):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)   # bloqueada aunque acierte
    reloj.avanzar(minutes=14)
    with pytest.raises(CuentaBloqueada, match="1 minuto\\."):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    reloj.avanzar(minutes=2)
    assert IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD).access_token  # ya pasó
    u = uow.usuarios.obtener_por_correo("ana@cbtis.mx")
    assert (u.intentos_fallidos, u.bloqueado_hasta) == (0, None)


def test_un_login_correcto_reinicia_el_contador(uow, hasher, tokens, crear_usuario, reloj):
    crear_usuario("ana@cbtis.mx")
    _fallar(uow, hasher, tokens, reloj, 4)
    IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    _fallar(uow, hasher, tokens, reloj, 4)                  # otra vez 4 sin bloquear
    assert uow.usuarios.obtener_por_correo("ana@cbtis.mx").bloqueado_hasta is None


def test_los_intentos_fallidos_de_un_correo_inexistente_no_bloquean_nada(uow, hasher, tokens, crear_usuario, reloj):
    crear_usuario("ana@cbtis.mx")
    _fallar(uow, hasher, tokens, reloj, 8, correo="nadie@cbtis.mx")
    assert IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD).access_token


def test_cambiar_password_cierra_las_otras_sesiones_y_entrega_tokens_nuevos(uow, hasher, tokens, crear_usuario, reloj):
    u = crear_usuario("ana@cbtis.mx")
    vieja = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    nueva = CambiarPassword(uow, hasher, tokens).ejecutar(u.id, PASSWORD, "otra-clave-larga-456")
    resolver, renovar = ObtenerUsuarioAutenticado(uow, tokens), RenovarToken(uow, tokens)
    with pytest.raises(NoAutenticado):
        resolver.ejecutar(vieja.access_token)
    with pytest.raises(NoAutenticado):
        renovar.ejecutar(vieja.refresh_token)
    assert resolver.ejecutar(nueva.access_token).id == u.id and renovar.ejecutar(nueva.refresh_token)


def test_restablecer_password_cierra_sesiones_y_desbloquea(uow, hasher, tokens, crear_usuario, reloj):
    from app.application.use_cases.usuarios.restablecer_password import RestablecerPassword
    from app.domain.exceptions import CuentaBloqueada

    u = crear_usuario("ana@cbtis.mx")
    sesion = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    _fallar(uow, hasher, tokens, reloj, 4)
    with pytest.raises(CuentaBloqueada):
        IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", "x")
    temporal = RestablecerPassword(uow, hasher).ejecutar(u.id)
    with pytest.raises(NoAutenticado):
        ObtenerUsuarioAutenticado(uow, tokens).ejecutar(sesion.access_token)
    assert IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", temporal).access_token


def test_desactivar_y_reactivar_no_revive_sesiones_anteriores(uow, hasher, tokens, crear_usuario, reloj):
    from app.application.use_cases.usuarios.actualizar_usuario import ActualizarUsuario

    admin = crear_usuario("admin@cbtis.mx", ["ADMINISTRADOR"], nombre="Admin")
    u = crear_usuario("ana@cbtis.mx")
    sesion = IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", PASSWORD)
    ActualizarUsuario(uow).ejecutar(admin.id, u.id, activo=False)
    ActualizarUsuario(uow).ejecutar(admin.id, u.id, activo=True)
    with pytest.raises(NoAutenticado):
        ObtenerUsuarioAutenticado(uow, tokens).ejecutar(sesion.access_token)
