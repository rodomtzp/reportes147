from datetime import date

import pytest

from app.application.use_cases.academico.asignaciones_tutor import (
    AsignarTutor, ListarAsignacionesTutor, RetirarAsignacionTutor,
)
from app.application.use_cases.academico.carreras import ActualizarCarrera, CrearCarrera, ListarCarreras
from app.application.use_cases.academico.grupos import ActualizarGrupo, CrearGrupo, ListarGrupos
from app.application.use_cases.academico.periodos import (
    ActualizarPeriodo, CrearPeriodo, EstablecerPeriodoVigente, ListarPeriodos,
)
from app.domain.entities.grupo import Grupo
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada


# ---------- Grupo (dominio) ----------
def test_clave_del_grupo_y_grupo_siguiente_conserva_la_letra():
    g = Grupo(carrera_id=1, semestre=1, letra="g")
    assert g.clave == "1G"
    assert g.clave_siguiente() == "2G"
    assert Grupo(carrera_id=1, semestre=6, letra="G").clave_siguiente() is None


@pytest.mark.parametrize("semestre,letra", [(0, "G"), (7, "G"), (1, "GG"), (1, ""), (1, "1")])
def test_grupo_invalido(semestre, letra):
    with pytest.raises(ReglaDeNegocioViolada):
        Grupo(carrera_id=1, semestre=semestre, letra=letra)


# ---------- Carreras y grupos ----------
def test_carrera_clave_unica_y_normalizada(uow):
    c = CrearCarrera(uow).ejecutar("Programación", " prog ")
    assert c.clave == "PROG"
    with pytest.raises(Conflicto):
        CrearCarrera(uow).ejecutar("Otra", "PROG")


def test_grupo_unico_por_semestre_y_letra_y_solo_en_carrera_activa(uow):
    c1 = CrearCarrera(uow).ejecutar("Programación", "PROG")
    c2 = CrearCarrera(uow).ejecutar("Contabilidad", "CONT")
    CrearGrupo(uow).ejecutar(c1.id, 1, "G")
    with pytest.raises(Conflicto):  # un grupo solo puede estar en una carrera
        CrearGrupo(uow).ejecutar(c2.id, 1, "g")
    CrearGrupo(uow).ejecutar(c1.id, 2, "G")  # 2G es otro grupo
    ActualizarCarrera(uow).ejecutar(c2.id, activa=False)
    with pytest.raises(ReglaDeNegocioViolada):
        CrearGrupo(uow).ejecutar(c2.id, 1, "H")
    with pytest.raises(NoEncontrado):
        CrearGrupo(uow).ejecutar(999, 1, "H")


def test_una_carrera_tiene_varios_grupos_y_se_listan_por_carrera(uow):
    c = CrearCarrera(uow).ejecutar("Programación", "PROG")
    for sem, letra in [(1, "G"), (1, "H"), (3, "G")]:
        CrearGrupo(uow).ejecutar(c.id, sem, letra)
    assert {g.clave for g in ListarGrupos(uow).ejecutar(carrera_id=c.id)} == {"1G", "1H", "3G"}
    assert len(ListarGrupos(uow).ejecutar(semestre=1)) == 2


def test_no_se_desactiva_una_carrera_con_grupos_activos(uow):
    c = CrearCarrera(uow).ejecutar("Programación", "PROG")
    g = CrearGrupo(uow).ejecutar(c.id, 1, "G")
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarCarrera(uow).ejecutar(c.id, activa=False)
    ActualizarGrupo(uow).ejecutar(g.id, activo=False)
    assert ActualizarCarrera(uow).ejecutar(c.id, activa=False).activa is False
    assert ListarCarreras(uow).ejecutar(solo_activas=True) == []


def test_actualizar_grupo_rechaza_clave_duplicada(uow):
    c = CrearCarrera(uow).ejecutar("Programación", "PROG")
    CrearGrupo(uow).ejecutar(c.id, 1, "G")
    g2 = CrearGrupo(uow).ejecutar(c.id, 1, "H")
    with pytest.raises(Conflicto):
        ActualizarGrupo(uow).ejecutar(g2.id, letra="G")
    # la falla no debe haber dejado el grupo modificado
    assert uow.grupos.obtener_por_id(g2.id).letra == "H"


# ---------- Periodos ----------
def test_periodo_valida_fechas_y_nombre_unico(uow):
    with pytest.raises(ReglaDeNegocioViolada):
        CrearPeriodo(uow).ejecutar("2026-A", date(2027, 1, 31), date(2026, 8, 1))
    CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    with pytest.raises(Conflicto):
        CrearPeriodo(uow).ejecutar("2026-A", date(2027, 2, 1), date(2027, 7, 1))


def test_solo_un_periodo_vigente_a_la_vez(uow):
    a = CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    b = CrearPeriodo(uow).ejecutar("2026-B", date(2027, 2, 1), date(2027, 7, 1))
    EstablecerPeriodoVigente(uow).ejecutar(a.id)
    EstablecerPeriodoVigente(uow).ejecutar(b.id)
    vigentes = [p.nombre for p in ListarPeriodos(uow).ejecutar() if p.vigente]
    assert vigentes == ["2026-B"]
    with pytest.raises(NoEncontrado):
        EstablecerPeriodoVigente(uow).ejecutar(999)


def test_actualizar_periodo_revalida_fechas(uow):
    p = CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarPeriodo(uow).ejecutar(p.id, fecha_fin=date(2026, 7, 1))


# ---------- Tutores ----------
def _escenario(uow, crear_usuario):
    docente = crear_usuario("doc@cbtis.mx", ["DOCENTE"], nombre="Profe")
    carrera = CrearCarrera(uow).ejecutar("Programación", "PROG")
    g1 = CrearGrupo(uow).ejecutar(carrera.id, 1, "G")
    g2 = CrearGrupo(uow).ejecutar(carrera.id, 1, "H")
    periodo = CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    return docente, g1, g2, periodo


def test_asignar_tutor_devuelve_detalle_y_un_docente_puede_tutorar_varios_grupos(uow, crear_usuario):
    docente, g1, g2, periodo = _escenario(uow, crear_usuario)
    d = AsignarTutor(uow).ejecutar(docente.id, g1.id, periodo.id)
    assert (d.usuario_nombre, d.grupo_clave, d.periodo_nombre) == ("Profe", "1G", "2026-A")
    AsignarTutor(uow).ejecutar(docente.id, g2.id, periodo.id)
    assert len(ListarAsignacionesTutor(uow).ejecutar(usuario_id=docente.id)) == 2


def test_un_grupo_tiene_un_solo_tutor_por_periodo(uow, crear_usuario):
    docente, g1, _, periodo = _escenario(uow, crear_usuario)
    otro = crear_usuario("otro@cbtis.mx", ["DOCENTE"], nombre="Otro")
    AsignarTutor(uow).ejecutar(docente.id, g1.id, periodo.id)
    with pytest.raises(Conflicto):
        AsignarTutor(uow).ejecutar(otro.id, g1.id, periodo.id)


def test_solo_docentes_activos_pueden_ser_tutores(uow, crear_usuario):
    docente, g1, _, periodo = _escenario(uow, crear_usuario)
    prefecto = crear_usuario("pref@cbtis.mx", ["PREFECTO"])
    with pytest.raises(ReglaDeNegocioViolada):
        AsignarTutor(uow).ejecutar(prefecto.id, g1.id, periodo.id)
    for args in [(999, g1.id, periodo.id), (docente.id, 999, periodo.id), (docente.id, g1.id, 999)]:
        with pytest.raises(NoEncontrado):
            AsignarTutor(uow).ejecutar(*args)


def test_retirar_asignacion(uow, crear_usuario):
    docente, g1, _, periodo = _escenario(uow, crear_usuario)
    d = AsignarTutor(uow).ejecutar(docente.id, g1.id, periodo.id)
    RetirarAsignacionTutor(uow).ejecutar(d.asignacion.id)
    assert ListarAsignacionesTutor(uow).ejecutar() == []
    with pytest.raises(NoEncontrado):
        RetirarAsignacionTutor(uow).ejecutar(d.asignacion.id)
