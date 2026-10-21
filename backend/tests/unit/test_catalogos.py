import pytest

from app.application.use_cases.catalogos.tipos_incidencia import (
    ActualizarTipoIncidencia, CrearTipoIncidencia, ListarTiposIncidencia,
)
from app.application.use_cases.catalogos.tipos_sancion import (
    ActualizarTipoSancion, CrearTipoSancion, ListarTiposSancion,
)
from app.domain.entities.tipo_incidencia import TipoIncidencia
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada


def test_nombre_de_incidencia_unico_sin_distinguir_mayusculas(uow):
    CrearTipoIncidencia(uow).ejecutar("Pelea")
    with pytest.raises(Conflicto):
        CrearTipoIncidencia(uow).ejecutar("  pelea ")


def test_opcion_otro_no_se_renombra_ni_se_desactiva_y_va_al_final(uow):
    uow.tipos_incidencia.guardar(TipoIncidencia(nombre="Otro", es_otro=True))  # sembrada primero
    CrearTipoIncidencia(uow).ejecutar("Pelea")
    otro = next(t for t in ListarTiposIncidencia(uow).ejecutar() if t.es_otro)
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarTipoIncidencia(uow).ejecutar(otro.id, activo=False)
    with pytest.raises(ReglaDeNegocioViolada):
        ActualizarTipoIncidencia(uow).ejecutar(otro.id, nombre="Distinto")
    assert [t.nombre for t in ListarTiposIncidencia(uow).ejecutar()] == ["Pelea", "Otro"]


def test_desactivar_incidencia_la_oculta_del_listado_activo(uow):
    t = CrearTipoIncidencia(uow).ejecutar("Asistencia")
    ActualizarTipoIncidencia(uow).ejecutar(t.id, activo=False)
    assert ListarTiposIncidencia(uow).ejecutar(solo_activos=True) == []
    assert len(ListarTiposIncidencia(uow).ejecutar()) == 1
    with pytest.raises(NoEncontrado):
        ActualizarTipoIncidencia(uow).ejecutar(999, activo=True)


def test_catalogo_de_sanciones(uow):
    s = CrearTipoSancion(uow).ejecutar("Suspensión de N días", requiere_dias=True)
    CrearTipoSancion(uow).ejecutar("Carta compromiso")
    with pytest.raises(Conflicto):
        CrearTipoSancion(uow).ejecutar("carta compromiso")
    assert s.requiere_dias is True
    ActualizarTipoSancion(uow).ejecutar(s.id, activo=False)
    assert [t.nombre for t in ListarTiposSancion(uow).ejecutar(solo_activos=True)] == ["Carta compromiso"]
