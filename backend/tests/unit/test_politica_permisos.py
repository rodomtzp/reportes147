from app.domain.policies.politica_permisos import Permiso, permisos_de, tiene_permiso
from app.domain.value_objects.rol import Rol


def test_prefecto_solo_puede_crear_reportes():
    assert permisos_de([Rol.PREFECTO]) == {Permiso.CREAR_REPORTE}


def test_prefecto_no_ve_reportes():
    assert not tiene_permiso([Rol.PREFECTO], Permiso.VER_TODOS_LOS_REPORTES)
    assert not tiene_permiso([Rol.PREFECTO], Permiso.VER_REPORTES_PROPIOS)


def test_docente_ve_solo_propios():
    assert tiene_permiso([Rol.DOCENTE], Permiso.VER_REPORTES_PROPIOS)
    assert not tiene_permiso([Rol.DOCENTE], Permiso.VER_TODOS_LOS_REPORTES)


def test_solo_orientacion_registra_llamadas_y_turna():
    for rol in Rol:
        esperado = rol == Rol.ORIENTACION
        assert tiene_permiso([rol], Permiso.REGISTRAR_LLAMADAS) == esperado
        assert tiene_permiso([rol], Permiso.TURNAR_A_SUBDIRECCION) == esperado


def test_solo_subdireccion_y_direccion_aplican_sanciones():
    con_permiso = {r for r in Rol if tiene_permiso([r], Permiso.APLICAR_SANCIONES)}
    assert con_permiso == {Rol.SUBDIRECCION, Rol.DIRECCION}


def test_datos_de_contacto_solo_para_orientacion_subdireccion_direccion():
    con_permiso = {r for r in Rol if tiene_permiso([r], Permiso.VER_DATOS_CONTACTO)}
    assert con_permiso == {Rol.ORIENTACION, Rol.SUBDIRECCION, Rol.DIRECCION}


def test_administrador_no_consulta_reportes():
    assert not tiene_permiso([Rol.ADMINISTRADOR], Permiso.VER_TODOS_LOS_REPORTES)
    assert tiene_permiso([Rol.ADMINISTRADOR], Permiso.GESTIONAR_USUARIOS)


def test_usuario_con_varios_roles_une_permisos():
    permisos = permisos_de([Rol.DOCENTE, Rol.PREFECTO])
    assert Permiso.VER_REPORTES_PROPIOS in permisos and Permiso.CREAR_REPORTE in permisos
