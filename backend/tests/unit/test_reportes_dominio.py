from datetime import datetime, timezone

import pytest

from app.domain.entities.reporte import Reporte
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_escalamiento import debe_alertar_subdireccion
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.policies.politica_transiciones import validar_transicion
from app.domain.value_objects.estado_reporte import EstadoReporte as E
from app.domain.value_objects.gravedad import Gravedad as G
from app.domain.value_objects.rol import Rol

AHORA = datetime(2026, 10, 6, 10, 0, tzinfo=timezone.utc)


def _reporte(**kw):
    base = dict(estudiante_id=1, inscripcion_id=1, creado_por=1, tipo_incidencia_id=1,
                descripcion="Se levantó durante la clase sin permiso.", fecha_hora_incidente=AHORA,
                gravedad=G.LEVE, incidente_id="x")
    base.update(kw)
    return Reporte(**base)


@pytest.mark.parametrize("anterior,nueva,esperado", [
    (None, G.LEVE, False), (None, G.MEDIA, False), (None, G.GRAVE, True), (None, G.MUY_GRAVE, True),
    (G.LEVE, G.GRAVE, True), (G.MEDIA, G.MUY_GRAVE, True),
    (G.GRAVE, G.MUY_GRAVE, False), (G.MUY_GRAVE, G.GRAVE, False),  # ya estaba escalado
    (G.GRAVE, G.LEVE, False),
])
def test_alerta_a_subdireccion_solo_al_escalar(anterior, nueva, esperado):
    assert debe_alertar_subdireccion(anterior, nueva) is esperado


def test_flujo_de_estados_es_lineal():
    validar_transicion(E.CREADO, E.EN_REVISION_ORIENTACION)
    validar_transicion(E.EN_REVISION_ORIENTACION, E.ATENDIDO_SUBDIRECCION)
    validar_transicion(E.ATENDIDO_SUBDIRECCION, E.SANCIONADO_CONCLUIDO)
    for origen, destino in [(E.CREADO, E.ATENDIDO_SUBDIRECCION), (E.EN_REVISION_ORIENTACION, E.CREADO),
                            (E.SANCIONADO_CONCLUIDO, E.CREADO), (E.ATENDIDO_SUBDIRECCION, E.EN_REVISION_ORIENTACION)]:
        with pytest.raises(ReglaDeNegocioViolada):
            validar_transicion(origen, destino)


@pytest.mark.parametrize("descripcion", ["corta", "   ", "x" * 2001])
def test_descripcion_con_longitud_invalida(descripcion):
    with pytest.raises(ReglaDeNegocioViolada):
        _reporte(descripcion=descripcion)


def test_cancelar_exige_motivo_y_bloquea_modificaciones():
    r = _reporte()
    with pytest.raises(ReglaDeNegocioViolada):
        r.cancelar("corto", 1, AHORA)
    r.cancelar("Capturado en el estudiante equivocado", 7, AHORA)
    assert r.cancelado and r.cancelado_por == 7
    for accion in (lambda: r.cambiar_gravedad(G.GRAVE), lambda: r.transicionar(E.EN_REVISION_ORIENTACION),
                   lambda: r.cancelar("Otro motivo suficientemente largo", 7, AHORA)):
        with pytest.raises(ReglaDeNegocioViolada):
            accion()


def test_un_reporte_concluido_no_se_modifica_ni_se_cancela():
    r = _reporte(estado=E.SANCIONADO_CONCLUIDO)
    with pytest.raises(ReglaDeNegocioViolada):
        r.cancelar("Motivo suficientemente largo", 1, AHORA)
    with pytest.raises(ReglaDeNegocioViolada):
        r.cambiar_gravedad(G.GRAVE)


def test_misma_gravedad_no_es_un_cambio():
    with pytest.raises(ReglaDeNegocioViolada):
        _reporte(gravedad=G.MEDIA).cambiar_gravedad(G.MEDIA)


def test_permisos_de_reportes():
    def roles_con(p):
        return {r for r in Rol if tiene_permiso([r], p)}
    assert roles_con(Permiso.CREAR_REPORTE) == {Rol.DOCENTE, Rol.PREFECTO, Rol.ORIENTACION, Rol.SUBDIRECCION, Rol.DIRECCION}
    assert roles_con(Permiso.CORREGIR_REPORTE) == {Rol.ORIENTACION, Rol.SUBDIRECCION, Rol.DIRECCION}
    assert roles_con(Permiso.VER_TODOS_LOS_REPORTES) == {Rol.ORIENTACION, Rol.SUBDIRECCION, Rol.DIRECCION}
    assert Rol.PREFECTO not in roles_con(Permiso.VER_REPORTES_PROPIOS)  # los prefectos solo generan
