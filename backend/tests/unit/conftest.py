import pytest

from app.application.use_cases.usuarios.crear_usuario import CrearUsuario
from app.infrastructure.security.token_jwt import TokenJWT
from tests.unit.fakes import HasherFalso, UoWMem

PASSWORD = "una-clave-larga-123"


@pytest.fixture
def uow():
    return UoWMem()


@pytest.fixture
def hasher():
    return HasherFalso()


@pytest.fixture
def tokens():
    return TokenJWT("x" * 40, access_minutos=15, refresh_horas=8)


@pytest.fixture
def crear_usuario(uow, hasher):
    def _crear(correo="ana@cbtis.mx", roles=("ORIENTACION",), nombre="Ana", **kw):
        return CrearUsuario(uow, hasher).ejecutar(nombre, correo, PASSWORD, list(roles), **kw)

    return _crear


@pytest.fixture
def escenario(uow, crear_usuario):
    """Carrera con grupos 1G, 2G, 6G y 1H; periodos 2026-A (vigente) y 2026-B; un docente tutor de 1G."""
    from datetime import date

    from app.application.use_cases.academico.asignaciones_tutor import AsignarTutor
    from app.application.use_cases.academico.carreras import CrearCarrera
    from app.application.use_cases.academico.grupos import CrearGrupo
    from app.application.use_cases.academico.periodos import CrearPeriodo, EstablecerPeriodoVigente

    carrera = CrearCarrera(uow).ejecutar("Programación", "PROG")
    grupos = {c: CrearGrupo(uow).ejecutar(carrera.id, int(c[0]), c[1]) for c in ["1G", "2G", "6G", "1H"]}
    a = CrearPeriodo(uow).ejecutar("2026-A", date(2026, 8, 1), date(2027, 1, 31))
    b = CrearPeriodo(uow).ejecutar("2026-B", date(2027, 2, 1), date(2027, 7, 1))
    EstablecerPeriodoVigente(uow).ejecutar(a.id)
    tutor = crear_usuario("tutor@cbtis.mx", ["DOCENTE"], nombre="Tutor 1G")
    AsignarTutor(uow).ejecutar(tutor.id, grupos["1G"].id, a.id)
    return {"carrera": carrera, "grupos": grupos, "a": a, "b": b, "tutor": tutor}


def datos_estudiante(control="24301080150001", **extra):
    base = {
        "numero_control": control, "primer_apellido": "Pérez", "segundo_apellido": "Gómez",
        "nombres": "Ana María", "generacion": "2024-2027",
    }
    base.update(extra)
    return base


TUTOR_LEGAL = {"nombre": "Laura Gómez", "telefono": "(449) 765-4321", "parentesco": "Madre"}


@pytest.fixture
def reloj():
    from datetime import datetime, timedelta, timezone

    from tests.unit.fakes import RelojFalso

    return RelojFalso(datetime(2026, 10, 6, 10, 0, tzinfo=timezone(timedelta(hours=-6))))


@pytest.fixture
def almacen():
    from tests.unit.fakes import AlmacenMem

    return AlmacenMem()


@pytest.fixture
def notificador():
    from tests.unit.fakes import NotificadorMem

    return NotificadorMem()


@pytest.fixture
def mundo(uow, escenario, crear_usuario):
    """Estudiantes en 1G (a, b, c) y 1H (d), tipos de incidencia y usuarios de varios roles."""
    from app.application.use_cases.estudiantes.crear_estudiante import CrearEstudiante
    from app.domain.entities.tipo_incidencia import TipoIncidencia

    est = {}
    for letra, grupo, apellido in [("a", "1G", "Alvarez"), ("b", "1G", "Beltrán"), ("c", "1G", "Cruz"), ("d", "1H", "Duarte")]:
        d = CrearEstudiante(uow).ejecutar(
            escenario["grupos"][grupo].id, [dict(TUTOR_LEGAL)],
            **datos_estudiante(f"2430108015000{ord(letra) - 96}", primer_apellido=apellido))
        est[letra] = d.estudiante
    pelea = uow.tipos_incidencia.guardar(TipoIncidencia(nombre="Pelea"))
    otro = uow.tipos_incidencia.guardar(TipoIncidencia(nombre="Otro", es_otro=True))
    usuarios = {
        "docente": crear_usuario("docente@cbtis.mx", ["DOCENTE"], nombre="Docente Uno"),
        "docente2": crear_usuario("docente2@cbtis.mx", ["DOCENTE"], nombre="Docente Dos"),
        "prefecto": crear_usuario("prefecto@cbtis.mx", ["PREFECTO"], nombre="Prefecto"),
        "orientacion": crear_usuario("orient@cbtis.mx", ["ORIENTACION"], nombre="Orientación"),
        "subdireccion": crear_usuario("sub@cbtis.mx", ["SUBDIRECCION"], nombre="Subdirección"),
        "tutor": escenario["tutor"],  # docente tutor de 1G
    }
    return {**escenario, "est": est, "pelea": pelea, "otro": otro, "u": usuarios}
