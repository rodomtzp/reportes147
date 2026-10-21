import pytest

from app.application.use_cases.academico.asignaciones_tutor import AsignarTutor
from app.application.use_cases.academico.carreras import CrearCarrera
from app.application.use_cases.academico.grupos import CrearGrupo
from app.application.use_cases.academico.periodos import CrearPeriodo, EstablecerPeriodoVigente
from app.application.use_cases.auth.iniciar_sesion import IniciarSesion
from app.application.use_cases.usuarios.actualizar_usuario import ActualizarUsuario
from app.application.use_cases.usuarios.crear_usuario import CrearUsuario
from app.application.use_cases.usuarios.listar_usuarios import ListarUsuarios
from app.application.use_cases.usuarios.registrar_usuario import RegistrarUsuario
from app.application.use_cases.usuarios.restablecer_password import RestablecerPassword
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.rol import Rol
from datetime import date
from tests.unit.conftest import PASSWORD


def test_crear_usuario_normaliza_correo_y_rechaza_duplicado(uow, hasher, crear_usuario):
    u = crear_usuario("Ana@Cbtis.mx ")
    assert u.correo == "ana@cbtis.mx"
    with pytest.raises(Conflicto):
        CrearUsuario(uow, hasher).ejecutar("Otra", "ana@cbtis.mx", PASSWORD, ["DOCENTE"])


@pytest.mark.parametrize("password,roles", [("corta", ["DOCENTE"]), (PASSWORD, [])])
def test_crear_usuario_valida_password_y_roles(uow, hasher, password, roles):
    with pytest.raises(ReglaDeNegocioViolada):
        CrearUsuario(uow, hasher).ejecutar("Luis", "luis@cbtis.mx", password, roles)


def test_registrar_usuario_genera_password_temporal_que_obliga_a_cambiarla(uow, hasher, tokens, reloj):
    usuario, temporal = RegistrarUsuario(uow, hasher).ejecutar("Luis", "luis@cbtis.mx", ["DOCENTE"])
    assert usuario.debe_cambiar_password and len(temporal) >= 10
    # la temporal permite iniciar sesión
    assert IniciarSesion(uow, hasher, tokens, reloj).ejecutar("luis@cbtis.mx", temporal).access_token


def test_restablecer_password_genera_nueva_temporal(uow, hasher, tokens, crear_usuario, reloj):
    u = crear_usuario("ana@cbtis.mx")
    temporal = RestablecerPassword(uow, hasher).ejecutar(u.id)
    assert uow.usuarios.obtener_por_id(u.id).debe_cambiar_password
    assert IniciarSesion(uow, hasher, tokens, reloj).ejecutar("ana@cbtis.mx", temporal).access_token
    with pytest.raises(NoEncontrado):
        RestablecerPassword(uow, hasher).ejecutar(999)


def test_listar_usuarios_filtra_por_rol_y_estado(uow, crear_usuario):
    crear_usuario("a@cbtis.mx", ["DOCENTE"], nombre="A")
    b = crear_usuario("b@cbtis.mx", ["PREFECTO"], nombre="B")
    ActualizarUsuario(uow).ejecutar(actor_id=999, usuario_id=b.id, activo=False)
    listar = ListarUsuarios(uow)
    assert [u.correo for u in listar.ejecutar(rol=Rol.DOCENTE)] == ["a@cbtis.mx"]
    assert [u.correo for u in listar.ejecutar(activo=False)] == ["b@cbtis.mx"]


def test_administrador_no_puede_desactivarse_ni_quitarse_su_rol(uow, crear_usuario):
    admin = crear_usuario("admin@cbtis.mx", ["ADMINISTRADOR"])
    caso = ActualizarUsuario(uow)
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(admin.id, admin.id, activo=False)
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(admin.id, admin.id, roles=["DOCENTE"])
    assert caso.ejecutar(admin.id, admin.id, nombre="Nuevo nombre").nombre == "Nuevo nombre"


def test_actualizar_usuario_cambia_roles_y_valida_que_no_queden_vacios(uow, crear_usuario):
    admin = crear_usuario("admin@cbtis.mx", ["ADMINISTRADOR"])
    u = crear_usuario("u@cbtis.mx", ["DOCENTE"])
    caso = ActualizarUsuario(uow)
    assert caso.ejecutar(admin.id, u.id, roles=["DOCENTE", "PREFECTO"]).roles == {Rol.DOCENTE, Rol.PREFECTO}
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(admin.id, u.id, roles=[])


def test_no_se_quita_rol_docente_a_un_tutor_del_periodo_vigente(uow, crear_usuario):
    admin = crear_usuario("admin@cbtis.mx", ["ADMINISTRADOR"])
    docente = crear_usuario("doc@cbtis.mx", ["DOCENTE"])
    carrera = CrearCarrera(uow).ejecutar("Programación", "PROG")
    grupo = CrearGrupo(uow).ejecutar(carrera.id, 1, "G")
    periodo = CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    EstablecerPeriodoVigente(uow).ejecutar(periodo.id)
    AsignarTutor(uow).ejecutar(docente.id, grupo.id, periodo.id)
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarUsuario(uow).ejecutar(admin.id, docente.id, roles=["PREFECTO"])
