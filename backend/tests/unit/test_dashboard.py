import pytest

from app.application.use_cases.dashboard.obtener_dashboard import ObtenerDashboard
from app.application.use_cases.reportes.crear_reportes import CrearReportes
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.gravedad import Gravedad as G

TEXTO = "Se peleó con un compañero durante el receso."


@pytest.fixture
def crear(uow, reloj, notificador, mundo):
    def _crear(letra, autor="docente", gravedad=G.LEVE, dias_atras=0):
        reloj.avanzar(minutes=1)
        from datetime import timedelta
        return CrearReportes(uow, reloj, notificador).ejecutar(
            mundo["u"][autor], [mundo["est"][letra].id], mundo["pelea"].id, TEXTO, gravedad,
            fecha_hora_incidente=reloj.ahora() - timedelta(days=dias_atras))[0].reporte_id
    return _crear


def _dash(uow, reloj, actor, rango="periodo"):
    return ObtenerDashboard(uow, reloj).ejecutar(actor, rango)


def test_directivo_ve_todo_el_plantel(uow, reloj, mundo, crear):
    crear("a"); crear("b", gravedad=G.GRAVE); crear("d")
    d = _dash(uow, reloj, mundo["u"]["orientacion"])
    assert d.alcance == "total" and d.total_rango == 3 and d.periodo_nombre == "2026-A"
    assert dict(d.por_gravedad) == {"Leve": 2, "Media": 0, "Grave": 1, "Muy grave": 0}
    assert dict(d.por_grupo) == {"1G": 2, "1H": 1} and dict(d.por_tipo) == {"Pelea": 3}
    assert dict(d.por_estado)["En revisión por Orientación"] == 3
    assert d.pendientes_llamada == 3 and d.alertas_pendientes is None   # Orientación no ve la bandeja
    assert sum(v for _, v in d.serie) == 3 and d.granularidad == "semana"


def test_subdireccion_ve_alertas_pendientes(uow, reloj, mundo, crear):
    from app.domain.entities.notificacion import Notificacion

    crear("a", gravedad=G.MUY_GRAVE)
    uow.notificaciones.guardar(Notificacion(
        tipo="REPORTE_GRAVE", titulo="Reporte muy grave", mensaje="x", rol_destino="SUBDIRECCION", creada_en=reloj.ahora()))
    assert _dash(uow, reloj, mundo["u"]["subdireccion"]).alertas_pendientes == 1


def test_docente_solo_ve_lo_que_creo_y_tutor_su_grupo(uow, reloj, mundo, crear):
    crear("a", "docente"); crear("a", "docente2"); crear("d", "docente")
    docente = _dash(uow, reloj, mundo["u"]["docente"])
    assert docente.alcance == "propio" and docente.total_rango == 2
    assert docente.pendientes_llamada is None and docente.alertas_pendientes is None
    tutor = _dash(uow, reloj, mundo["u"]["tutor"])          # tutor de 1G: los dos de "a"
    assert tutor.total_rango == 2 and dict(tutor.por_grupo) == {"1G": 2}


def test_prefecto_no_ve_datos(uow, reloj, mundo, crear):
    crear("a")
    d = _dash(uow, reloj, mundo["u"]["prefecto"])
    assert d.alcance == "ninguno" and d.total_rango == 0 and d.serie == []


def test_comparacion_con_el_mes_anterior_y_rangos(uow, reloj, mundo, crear):
    crear("a"); crear("b")                       # octubre
    crear("a", dias_atras=10)                    # finales de septiembre
    o = mundo["u"]["orientacion"]
    d = _dash(uow, reloj, o, "mes")
    assert (d.mes_actual, d.mes_anterior, d.total_rango, d.granularidad) == (2, 1, 2, "dia")
    assert _dash(uow, reloj, o, "30dias").total_rango == 3
    assert _dash(uow, reloj, o, "periodo").total_rango == 3
    with pytest.raises(ReglaDeNegocioViolada):
        _dash(uow, reloj, o, "siempre")


def test_estudiantes_en_riesgo(uow, reloj, mundo, crear):
    for _ in range(2):
        crear("a")
    for _ in range(3):
        crear("b")
    crear("c")
    d = _dash(uow, reloj, mundo["u"]["subdireccion"])
    assert [(e.estudiante, e.total) for e in d.en_riesgo] == [("Beltrán Gómez Ana María", 3), ("Alvarez Gómez Ana María", 2)]
    assert d.total_en_riesgo == 2 and d.listos_para_sancion == 1 and d.en_riesgo[0].grupo == "1G"


def test_serie_incluye_cubetas_vacias(uow, reloj, mundo, crear):
    crear("a", dias_atras=20)
    d = _dash(uow, reloj, mundo["u"]["orientacion"], "30dias")
    assert len(d.serie) == 30 and sum(v for _, v in d.serie) == 1 and d.serie[-1][1] == 0
