import pytest

from app.domain.entities.estudiante import Estudiante
from app.domain.entities.grupo import Grupo
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_avance_semestre import decidir_destino
from app.domain.policies.politica_contacto import normalizar_correo, normalizar_telefono
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estatus_estudiante import AccionAvance, EstatusEstudiante
from app.domain.value_objects.rol import Rol


@pytest.mark.parametrize("entrada,esperado", [
    ("449 123 4567", "4491234567"), ("(449) 123-4567", "4491234567"),
    ("+52 449 123 4567", "4491234567"), ("+521 449 123 4567", "4491234567"),
])
def test_telefono_se_normaliza_a_10_digitos(entrada, esperado):
    assert normalizar_telefono(entrada) == esperado


@pytest.mark.parametrize("malo", ["123", "", "44912345678901", "abcdefghij"])
def test_telefono_invalido(malo):
    with pytest.raises(ReglaDeNegocioViolada):
        normalizar_telefono(malo)


def test_correo_opcional_y_validado():
    assert normalizar_correo("  ") is None and normalizar_correo(None) is None
    assert normalizar_correo(" ANA@Correo.com ") == "ana@correo.com"
    with pytest.raises(ReglaDeNegocioViolada):
        normalizar_correo("sin-arroba")


def test_estudiante_normaliza_y_valida():
    e = Estudiante(numero_control=" 24301080150001 ", primer_apellido="  Pérez  ", nombres="Ana   María",
                   generacion="2024-2027", telefono="449 123 4567", segundo_apellido="  ")
    assert e.nombre_completo == "Pérez Ana María" and e.segundo_apellido is None
    assert e.telefono == "4491234567" and e.estatus == EstatusEstudiante.ACTIVO


@pytest.mark.parametrize("campo,valor", [("numero_control", "123"), ("primer_apellido", " "), ("nombres", ""), ("generacion", "")])
def test_estudiante_rechaza_datos_obligatorios_invalidos(campo, valor):
    datos = dict(numero_control="24301080150001", primer_apellido="Pérez", nombres="Ana", generacion="2024-2027")
    datos[campo] = valor
    with pytest.raises(ReglaDeNegocioViolada):
        Estudiante(**datos)


def test_tutor_legal_exige_nombre_y_telefono_valido():
    assert TutorLegal(nombre="Laura", telefono="449-765-4321").telefono == "4497654321"
    with pytest.raises(ReglaDeNegocioViolada):
        TutorLegal(nombre="", telefono="4497654321")
    with pytest.raises(ReglaDeNegocioViolada):
        TutorLegal(nombre="Laura", telefono="123")


def test_avance_conserva_la_letra_y_sexto_semestre_egresa():
    g1 = Grupo(carrera_id=1, semestre=1, letra="G")
    d = decidir_destino(g1)
    assert (d.accion, d.clave_grupo, d.nuevo_estatus) == ("AVANZA", "2G", None)
    d6 = decidir_destino(Grupo(carrera_id=1, semestre=6, letra="G"))
    assert (d6.accion, d6.clave_grupo, d6.nuevo_estatus) == ("EGRESA", None, EstatusEstudiante.EGRESADO)


def test_avance_con_excepciones():
    g = Grupo(carrera_id=1, semestre=3, letra="H")
    rep = decidir_destino(g, AccionAvance.REPETIR)
    assert (rep.accion, rep.clave_grupo) == ("REPITE", "3H")
    baja = decidir_destino(g, AccionAvance.BAJA)
    assert (baja.accion, baja.clave_grupo, baja.nuevo_estatus) == ("BAJA", None, EstatusEstudiante.BAJA)
    # repetir sexto semestre: se queda en 6x y no egresa
    assert decidir_destino(Grupo(carrera_id=1, semestre=6, letra="G"), AccionAvance.REPETIR).clave_grupo == "6G"


def test_permisos_de_estudiantes():
    gestionan = {r for r in Rol if tiene_permiso([r], Permiso.GESTIONAR_ESTUDIANTES)}
    assert gestionan == {Rol.ADMINISTRADOR, Rol.ORIENTACION, Rol.SUBDIRECCION}
    for permiso in (Permiso.IMPORTAR_ESTUDIANTES, Permiso.AVANZAR_SEMESTRE):
        assert {r for r in Rol if tiene_permiso([r], permiso)} == {Rol.ADMINISTRADOR}
