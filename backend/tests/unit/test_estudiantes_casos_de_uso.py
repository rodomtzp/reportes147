import pytest

from app.application.use_cases.estudiantes.actualizar_estudiante import ActualizarEstudiante, CambiarGrupoEstudiante
from app.application.use_cases.estudiantes.consultas import BuscarEstudiantes, ListarEstudiantes, ObtenerEstudiante
from app.application.use_cases.estudiantes.crear_estudiante import CrearEstudiante
from app.application.use_cases.estudiantes.tutores_legales import (
    ActualizarTutorLegal, AgregarTutorLegal, EliminarTutorLegal,
)
from app.domain.exceptions import Conflicto, NoEncontrado, PermisoDenegado, ReglaDeNegocioViolada
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
from tests.unit.conftest import TUTOR_LEGAL, datos_estudiante


def _crear(uow, esc, clave="1G", control="24301080150001", **extra):
    return CrearEstudiante(uow).ejecutar(esc["grupos"][clave].id, [dict(TUTOR_LEGAL)], **datos_estudiante(control, **extra))


def test_crear_estudiante_con_tutor_principal_e_inscripcion(uow, escenario):
    d = _crear(uow, escenario)
    assert d.grupo_actual == "1G" and d.carrera_actual == "Programación"
    assert [t.es_principal for t in d.tutores_legales] == [True]
    assert d.tutores_legales[0].telefono == "4497654321"
    assert [(i.periodo_nombre, i.grupo_clave) for i in d.inscripciones] == [("2026-A", "1G")]


def test_crear_estudiante_reglas(uow, escenario):
    _crear(uow, escenario)
    with pytest.raises(Conflicto):
        _crear(uow, escenario)  # mismo número de control
    with pytest.raises(ReglaDeNegocioViolada):
        CrearEstudiante(uow).ejecutar(escenario["grupos"]["1G"].id, [], **datos_estudiante("24301080150002"))
    with pytest.raises(NoEncontrado):
        CrearEstudiante(uow).ejecutar(999, [dict(TUTOR_LEGAL)], **datos_estudiante("24301080150003"))


def test_crear_estudiante_requiere_periodo_vigente(uow):
    with pytest.raises(ReglaDeNegocioViolada):
        CrearEstudiante(uow).ejecutar(1, [dict(TUTOR_LEGAL)], **datos_estudiante())


def test_un_solo_tutor_principal_aunque_se_marquen_varios(uow, escenario):
    t2 = {"nombre": "Pedro Pérez", "telefono": "4491112233", "es_principal": True}
    d = CrearEstudiante(uow).ejecutar(
        escenario["grupos"]["1G"].id, [{**TUTOR_LEGAL, "es_principal": True}, t2], **datos_estudiante())
    assert [t.es_principal for t in d.tutores_legales].count(True) == 1


def test_actualizar_estudiante_no_permite_cambiar_numero_de_control(uow, escenario):
    d = _crear(uow, escenario)
    nuevo = ActualizarEstudiante(uow).ejecutar(d.estudiante.id, nombres="Ana Sofía", telefono="449 000 1122")
    assert nuevo.estudiante.nombres == "Ana Sofía" and nuevo.estudiante.telefono == "4490001122"
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarEstudiante(uow).ejecutar(d.estudiante.id, numero_control="99999999")
    with pytest.raises(NoEncontrado):
        ActualizarEstudiante(uow).ejecutar(999, nombres="X")


def test_cambiar_grupo_corrige_la_inscripcion_del_periodo_vigente(uow, escenario):
    d = _crear(uow, escenario, "1G")
    nuevo = CambiarGrupoEstudiante(uow).ejecutar(d.estudiante.id, escenario["grupos"]["1H"].id)
    assert nuevo.grupo_actual == "1H" and len(nuevo.inscripciones) == 1  # no duplica el historial
    ActualizarEstudiante(uow).ejecutar(d.estudiante.id, estatus=EstatusEstudiante.BAJA)
    with pytest.raises(ReglaDeNegocioViolada):
        CambiarGrupoEstudiante(uow).ejecutar(d.estudiante.id, escenario["grupos"]["1G"].id)


# ---------- tutores legales ----------
def test_agregar_cambiar_principal_y_eliminar_tutores(uow, escenario):
    d = _crear(uow, escenario)
    eid = d.estudiante.id
    tutores = AgregarTutorLegal(uow).ejecutar(eid, nombre="Pedro Pérez", telefono="4491112233", parentesco="Padre")
    assert [t.nombre for t in tutores if t.es_principal] == ["Laura Gómez"]  # el nuevo no lo es por defecto

    padre = next(t for t in tutores if t.nombre == "Pedro Pérez")
    tutores = ActualizarTutorLegal(uow).ejecutar(padre.id, es_principal=True)
    assert [t.nombre for t in tutores if t.es_principal] == ["Pedro Pérez"]

    tutores = EliminarTutorLegal(uow).ejecutar(padre.id)  # al borrar al principal, el otro se promueve
    assert [(t.nombre, t.es_principal) for t in tutores] == [("Laura Gómez", True)]
    with pytest.raises(ReglaDeNegocioViolada):
        EliminarTutorLegal(uow).ejecutar(tutores[0].id)  # debe quedar al menos uno


def test_no_se_puede_quitar_la_marca_de_principal_al_unico(uow, escenario):
    d = _crear(uow, escenario)
    unico = d.tutores_legales[0]
    tutores = ActualizarTutorLegal(uow).ejecutar(unico.id, es_principal=False)
    assert tutores[0].es_principal is True


# ---------- acceso y búsqueda ----------
def test_acceso_total_para_orientacion_y_tutor_solo_a_su_grupo(uow, reloj, escenario, crear_usuario):
    e1 = _crear(uow, escenario, "1G", "24301080150001").estudiante
    e2 = _crear(uow, escenario, "1H", "24301080150002", primer_apellido="Zúñiga").estudiante
    orientacion = crear_usuario("o@cbtis.mx", ["ORIENTACION"])
    tutor = escenario["tutor"]

    assert len(ListarEstudiantes(uow).ejecutar(orientacion)) == 2
    assert [i.estudiante.id for i in ListarEstudiantes(uow).ejecutar(tutor)] == [e1.id]
    assert ObtenerEstudiante(uow, reloj).ejecutar(tutor, e1.id).estudiante.id == e1.id
    with pytest.raises(PermisoDenegado):
        ObtenerEstudiante(uow, reloj).ejecutar(tutor, e2.id)  # de otro grupo
    with pytest.raises(PermisoDenegado):
        ListarEstudiantes(uow).ejecutar(tutor, grupo_id=escenario["grupos"]["1H"].id)


def test_docente_sin_grupos_y_prefecto_no_ven_estudiantes(uow, reloj, escenario, crear_usuario):
    e = _crear(uow, escenario).estudiante
    for correo, rol in [("d@cbtis.mx", "DOCENTE"), ("p@cbtis.mx", "PREFECTO")]:
        u = crear_usuario(correo, [rol])
        with pytest.raises(PermisoDenegado):
            ListarEstudiantes(uow).ejecutar(u)
        with pytest.raises(PermisoDenegado):
            ObtenerEstudiante(uow, reloj).ejecutar(u, e.id)


def test_filtros_de_listado(uow, escenario, crear_usuario):
    _crear(uow, escenario, "1G", "24301080150001")
    _crear(uow, escenario, "2G", "24301080150002", primer_apellido="López", nombres="Luis")
    o = crear_usuario("o@cbtis.mx", ["ORIENTACION"])
    listar = ListarEstudiantes(uow)
    assert [i.grupo_clave for i in listar.ejecutar(o, grupo_id=escenario["grupos"]["2G"].id)] == ["2G"]
    assert len(listar.ejecutar(o, carrera_id=escenario["carrera"].id)) == 2
    assert [i.estudiante.primer_apellido for i in listar.ejecutar(o, texto="lopez luis".replace("lopez", "López"))] == ["López"]


def test_buscador_devuelve_datos_minimos_solo_de_activos(uow, escenario):
    d = _crear(uow, escenario)
    resultados = BuscarEstudiantes(uow).ejecutar("pérez")
    assert len(resultados) == 1
    r = resultados[0]
    assert (r.numero_control, r.grupo_clave, r.carrera_nombre) == ("24301080150001", "1G", "Programación")
    assert not hasattr(r, "telefono") and not hasattr(r, "calle")  # sin datos de contacto
    ActualizarEstudiante(uow).ejecutar(d.estudiante.id, estatus=EstatusEstudiante.BAJA)
    assert BuscarEstudiantes(uow).ejecutar("pérez") == []
    with pytest.raises(ReglaDeNegocioViolada):
        BuscarEstudiantes(uow).ejecutar("p")
