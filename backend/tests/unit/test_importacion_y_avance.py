import pytest

from app.application.use_cases.academico.grupos import CrearGrupo
from app.application.use_cases.academico.periodos import EstablecerPeriodoVigente
from app.application.use_cases.estudiantes.avanzar_semestre import AvanzarSemestre
from app.application.use_cases.estudiantes.consultas import ObtenerEstudiante
from app.application.use_cases.estudiantes.crear_estudiante import CrearEstudiante
from app.application.use_cases.estudiantes.importar_estudiantes import ImportarEstudiantes
from app.application.use_cases.estudiantes.plantilla import plantilla_importacion_csv
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.estatus_estudiante import AccionAvance, EstatusEstudiante
from app.infrastructure.importacion.lector_estudiantes import LectorEstudiantes
from tests.unit.conftest import TUTOR_LEGAL, datos_estudiante

ENCABEZADO = "numero_control,primer_apellido,segundo_apellido,nombres,telefono,correo,calle,numero,colonia,ciudad,generacion,grupo,tutor_nombre,tutor_parentesco,tutor_telefono,tutor_correo"


def _csv(*filas: str, encabezado=ENCABEZADO) -> bytes:
    return ("\n".join([encabezado, *filas]) + "\n").encode("utf-8")


def fila(control, grupo="1G", tutor_tel="4497654321", apellido="Pérez"):
    return f"{control},{apellido},Gómez,Ana,4491234567,,,,,,2024-2027,{grupo},Laura,Madre,{tutor_tel},"


# ---------- lector ----------
def test_lector_csv_acepta_comas_punto_y_coma_y_encabezados_con_alias():
    lector = LectorEstudiantes()
    contenido = "No. Control;Apellido Paterno;Nombre(s);Generación;Grupo;Tutor;Teléfono Tutor\n24301;Pérez;Ana;2024-2027;1G;Laura;4497654321\n".encode("cp1252")
    filas = lector.leer(contenido, "alumnos.CSV")
    assert filas[0]["primer_apellido"] == "Pérez" and filas[0]["tutor_telefono"] == "4497654321"
    assert filas[0]["segundo_apellido"] == ""  # columnas ausentes quedan vacías


def test_lector_rechaza_archivos_invalidos():
    lector = LectorEstudiantes()
    with pytest.raises(ReglaDeNegocioViolada):
        lector.leer(b"", "a.csv")
    with pytest.raises(ReglaDeNegocioViolada):
        lector.leer(b"x", "a.pdf")
    with pytest.raises(ReglaDeNegocioViolada) as e:
        lector.leer(b"numero_control,nombres\n1,Ana\n", "a.csv")
    assert "primer_apellido" in str(e.value)
    with pytest.raises(ReglaDeNegocioViolada):
        lector.leer(b"x" * (2 * 1024 * 1024 + 1), "a.csv")


def test_la_plantilla_generada_es_importable():
    filas = LectorEstudiantes().leer(plantilla_importacion_csv().encode("utf-8"), "plantilla.csv")
    assert len(filas) == 1 and filas[0]["grupo"] == "1G"


# ---------- importación ----------
def test_importar_crea_nuevos_omite_existentes_y_reporta_errores(uow, escenario):
    CrearEstudiante(uow).ejecutar(escenario["grupos"]["1G"].id, [dict(TUTOR_LEGAL)], **datos_estudiante("24301080150001"))
    contenido = _csv(
        fila("24301080150001"),                          # ya existe → omitido
        fila("24301080150002"),                          # válido
        fila("24301080150002"),                          # repetido en el archivo → omitido
        fila("24301080150003", grupo="9Z"),              # grupo inexistente → error
        fila("24301080150004", tutor_tel="123"),         # teléfono de tutor inválido → error
        fila("24301080150005", grupo="2G", apellido="López"),  # válido
    )
    r = ImportarEstudiantes(uow, LectorEstudiantes()).ejecutar(contenido, "alumnos.csv")
    assert r.creados == 2
    assert [(o.fila, o.motivo) for o in r.omitidos] == [(2, "Ya existe en el sistema."), (4, "Repetido en el archivo.")]
    assert [e.fila for e in r.errores] == [5, 6]
    assert "9Z" in r.errores[0].motivo
    nuevo = uow.estudiantes.obtener_por_numero_control("24301080150005")
    assert uow.inscripciones.obtener(nuevo.id, escenario["a"].id).grupo_id == escenario["grupos"]["2G"].id
    assert uow.tutores_legales.listar_por_estudiante(nuevo.id)[0].es_principal
    # las filas con error no dejaron datos a medias
    assert uow.estudiantes.obtener_por_numero_control("24301080150003") is None
    assert uow.estudiantes.obtener_por_numero_control("24301080150004") is None


def test_importar_exige_periodo_vigente(uow):
    with pytest.raises(ReglaDeNegocioViolada):
        ImportarEstudiantes(uow, LectorEstudiantes()).ejecutar(_csv(fila("24301080150001")), "a.csv")


# ---------- avance de semestre ----------
def _poblar(uow, esc):
    ids = {}
    for control, clave in [("24301080150001", "1G"), ("24301080150002", "1G"), ("24301080150003", "1G"),
                           ("24301080150004", "2G"), ("24301080150005", "6G")]:
        d = CrearEstudiante(uow).ejecutar(esc["grupos"][clave].id, [dict(TUTOR_LEGAL)], **datos_estudiante(control))
        ids[control[-1]] = d.estudiante.id
    # la letra se conserva: 1G→2G, 2G→3G (hay que crear 3G), 6G egresa
    CrearGrupo(uow).ejecutar(esc["carrera"].id, 3, "G")
    return ids


def test_simulacion_no_modifica_nada_y_resume_los_movimientos(uow, escenario):
    ids = _poblar(uow, escenario)
    r = AvanzarSemestre(uow).ejecutar(escenario["a"].id, escenario["b"].id, {ids["2"]: AccionAvance.REPETIR, ids["3"]: AccionAvance.BAJA})
    assert not r.ejecutado and r.grupos_faltantes == []
    por_control = {m.numero_control[-1]: (m.grupo_origen, m.grupo_destino, m.accion) for m in r.movimientos}
    assert por_control == {
        "1": ("1G", "2G", "AVANZA"), "2": ("1G", "1G", "REPITE"), "3": ("1G", None, "BAJA"),
        "4": ("2G", "3G", "AVANZA"), "5": ("6G", None, "EGRESA"),
    }
    assert uow.inscripciones.listar_por_periodo(escenario["b"].id) == []
    assert uow.estudiantes.obtener_por_id(ids["3"]).estatus == EstatusEstudiante.ACTIVO


def test_ejecucion_conserva_el_historial_y_actualiza_estatus(uow, reloj, escenario):
    ids = _poblar(uow, escenario)
    AvanzarSemestre(uow).ejecutar(
        escenario["a"].id, escenario["b"].id,
        {ids["2"]: AccionAvance.REPETIR, ids["3"]: AccionAvance.BAJA}, simular=False)

    EstablecerPeriodoVigente(uow).ejecutar(escenario["b"].id)
    admin = type("A", (), {"roles": frozenset(), "id": 0})()  # acceso lo da el rol; usamos orientación abajo
    from app.domain.entities.usuario import Usuario
    o = Usuario(nombre="O", correo="o@x.mx", password_hash="x", roles=frozenset(["ORIENTACION"]), id=99)

    historial = lambda i: [(h.periodo_nombre, h.grupo_clave) for h in ObtenerEstudiante(uow, reloj).ejecutar(o, i).inscripciones]  # noqa: E731
    assert historial(ids["1"]) == [("2026-A", "1G"), ("2026-B", "2G")]   # 1G → 2G, historial intacto
    assert historial(ids["2"]) == [("2026-A", "1G"), ("2026-B", "1G")]   # repite
    assert historial(ids["3"]) == [("2026-A", "1G")]                       # baja: sin nueva inscripción
    assert uow.estudiantes.obtener_por_id(ids["3"]).estatus == EstatusEstudiante.BAJA
    assert uow.estudiantes.obtener_por_id(ids["5"]).estatus == EstatusEstudiante.EGRESADO
    assert ObtenerEstudiante(uow, reloj).ejecutar(o, ids["1"]).grupo_actual == "2G"


def test_avance_es_idempotente(uow, escenario):
    _poblar(uow, escenario)
    caso = AvanzarSemestre(uow)
    caso.ejecutar(escenario["a"].id, escenario["b"].id, {}, simular=False)
    segunda = caso.ejecutar(escenario["a"].id, escenario["b"].id, {}, simular=False)
    assert segunda.movimientos == [] and segunda.omitidos_ya_inscritos == 4  # el egresado ya no es activo
    assert len(uow.inscripciones.listar_por_periodo(escenario["b"].id)) == 4


def test_avance_falla_si_faltan_grupos_pero_la_simulacion_los_lista(uow, escenario):
    CrearEstudiante(uow).ejecutar(escenario["grupos"]["2G"].id, [dict(TUTOR_LEGAL)], **datos_estudiante())  # no existe 3G
    sim = AvanzarSemestre(uow).ejecutar(escenario["a"].id, escenario["b"].id, {})
    assert sim.grupos_faltantes == ["3G"]
    with pytest.raises(ReglaDeNegocioViolada) as e:
        AvanzarSemestre(uow).ejecutar(escenario["a"].id, escenario["b"].id, {}, simular=False)
    assert "3G" in str(e.value)
    assert uow.inscripciones.listar_por_periodo(escenario["b"].id) == []  # nada a medias


def test_avance_valida_periodos_y_excepciones(uow, escenario):
    ids = _poblar(uow, escenario)
    a, b = escenario["a"].id, escenario["b"].id
    caso = AvanzarSemestre(uow)
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(b, a, {})          # destino anterior al origen
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(a, a, {})
    with pytest.raises(NoEncontrado):
        caso.ejecutar(a, 999, {})
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(a, b, {99999: AccionAvance.BAJA})  # estudiante ajeno al periodo de origen
