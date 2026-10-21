from datetime import datetime, timedelta, timezone

import pytest

from app.application.use_cases.academico.carreras import CrearCarrera  # noqa: F401
from app.application.use_cases.reportes.adjuntos import AgregarAdjunto, ObtenerAdjunto
from app.application.use_cases.reportes.consultas import ListarReportes, ObtenerReporte
from app.application.use_cases.reportes.crear_reportes import CrearReportes
from app.application.use_cases.reportes.gestion import (
    CambiarGravedad, CancelarReporte, CorregirReporte, TurnarASubdireccion,
)
from app.domain.exceptions import NoEncontrado, PermisoDenegado, ReglaDeNegocioViolada
from app.domain.value_objects.estado_reporte import EstadoReporte, TipoEventoReporte
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
from app.domain.value_objects.gravedad import Gravedad as G

TEXTO = "Se peleó con un compañero durante el receso."
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.4\n" + b"0" * 64


def _crear(uow, reloj, notificador, actor, mundo, letras="a", gravedad=G.LEVE, tipo="pelea", **kw):
    ids = [mundo["est"][l].id for l in letras]
    return CrearReportes(uow, reloj, notificador).ejecutar(
        actor, ids, mundo[tipo].id, kw.pop("descripcion", TEXTO), gravedad, **kw)


def _historial(uow, reporte_id):
    return [(e.tipo, e.campo, e.valor_anterior, e.valor_nuevo) for e in uow.historial_reportes.listar_por_reporte(reporte_id)]


# ---------- creación ----------
def test_crear_un_reporte_por_estudiante_con_folio_incidente_y_estado(uow, reloj, notificador, mundo):
    docente = mundo["u"]["docente"]
    creados = _crear(uow, reloj, notificador, docente, mundo, "ab")
    assert [c.folio for c in creados] == ["RPT-2026-0001", "RPT-2026-0002"]
    r1, r2 = (uow.reportes.obtener_por_id(c.reporte_id) for c in creados)
    assert r1.incidente_id == r2.incidente_id and r1.estudiante_id != r2.estudiante_id
    assert r1.estado == EstadoReporte.EN_REVISION_ORIENTACION  # entra directo a Orientación
    assert r1.inscripcion_id == uow.inscripciones.obtener(r1.estudiante_id, mundo["a"].id).id
    assert _historial(uow, r1.id) == [
        (TipoEventoReporte.CREACION, None, None, "RPT-2026-0001"),
        (TipoEventoReporte.ESTADO, "estado", "CREADO", "EN_REVISION_ORIENTACION"),
    ]


def test_el_folio_reinicia_cada_anio(uow, reloj, notificador, mundo):
    d = mundo["u"]["docente"]
    _crear(uow, reloj, notificador, d, mundo, "a")
    reloj.fijar(datetime(2027, 1, 5, 9, 0, tzinfo=reloj.ahora().tzinfo))
    assert _crear(uow, reloj, notificador, d, mundo, "b")[0].folio == "RPT-2027-0001"
    reloj.fijar(datetime(2026, 12, 31, 9, 0, tzinfo=reloj.ahora().tzinfo))
    assert _crear(uow, reloj, notificador, d, mundo, "c")[0].folio == "RPT-2026-0002"


def test_alerta_a_subdireccion_solo_con_grave_o_muy_grave(uow, reloj, notificador, mundo):
    d = mundo["u"]["docente"]
    _crear(uow, reloj, notificador, d, mundo, "a", G.MEDIA)
    assert notificador.alertas == []
    _crear(uow, reloj, notificador, d, mundo, "bc", G.MUY_GRAVE)
    assert [(a.estudiante.split()[0], a.gravedad, a.grupo) for a in notificador.alertas] == [
        ("Beltrán", G.MUY_GRAVE, "1G"), ("Cruz", G.MUY_GRAVE, "1G")]


def test_si_falla_el_aviso_el_reporte_se_crea_igual(uow, reloj, notificador, mundo):
    notificador.falla = True
    creados = _crear(uow, reloj, notificador, mundo["u"]["docente"], mundo, "a", G.GRAVE)
    assert uow.reportes.obtener_por_id(creados[0].reporte_id) is not None


def test_crear_valida_tipo_otro_y_fecha(uow, reloj, notificador, mundo):
    d = mundo["u"]["docente"]
    with pytest.raises(ReglaDeNegocioViolada):  # 'Otro' exige descripción
        _crear(uow, reloj, notificador, d, mundo, "a", tipo="otro")
    r = _crear(uow, reloj, notificador, d, mundo, "a", tipo="otro", descripcion_otro="  Uso de celular  ")
    assert uow.reportes.obtener_por_id(r[0].reporte_id).descripcion_otro == "Uso de celular"
    ignorado = _crear(uow, reloj, notificador, d, mundo, "b", descripcion_otro="se ignora")  # tipo normal
    assert uow.reportes.obtener_por_id(ignorado[0].reporte_id).descripcion_otro is None
    with pytest.raises(ReglaDeNegocioViolada):
        _crear(uow, reloj, notificador, d, mundo, "c", fecha_hora_incidente=reloj.ahora() + timedelta(hours=1))
    ayer = datetime(2026, 10, 5, 8, 30)  # sin zona: se interpreta en la zona local
    ok = _crear(uow, reloj, notificador, d, mundo, "c", fecha_hora_incidente=ayer)
    assert uow.reportes.obtener_por_id(ok[0].reporte_id).fecha_hora_incidente.tzinfo is not None


def test_crear_rechaza_estudiantes_invalidos_y_no_deja_nada_a_medias(uow, reloj, notificador, mundo):
    d = mundo["u"]["docente"]
    est_d = mundo["est"]["d"]
    est_d.estatus = EstatusEstudiante.BAJA
    uow.estudiantes.guardar(est_d)
    with pytest.raises(ReglaDeNegocioViolada):
        _crear(uow, reloj, notificador, d, mundo, "ad")  # 'd' en baja
    with pytest.raises(NoEncontrado):
        CrearReportes(uow, reloj, notificador).ejecutar(
            d, [mundo["est"]["a"].id, 9999], mundo["pelea"].id, TEXTO, G.LEVE)
    with pytest.raises(ReglaDeNegocioViolada):
        CrearReportes(uow, reloj, notificador).ejecutar(d, [], mundo["pelea"].id, TEXTO, G.LEVE)
    with pytest.raises(ReglaDeNegocioViolada):
        CrearReportes(uow, reloj, notificador).ejecutar(d, [mundo["est"]["a"].id], mundo["pelea"].id, "corta", G.LEVE)
    assert uow.reportes._todos() == []


def test_ids_repetidos_se_ignoran(uow, reloj, notificador, mundo):
    creados = _crear(uow, reloj, notificador, mundo["u"]["docente"], mundo, "aaa")
    assert len(creados) == 1


# ---------- acceso ----------
def test_quien_ve_que_reportes(uow, reloj, notificador, mundo):
    u = mundo["u"]
    _crear(uow, reloj, notificador, u["docente"], mundo, "a")        # docente → alumno de 1G
    _crear(uow, reloj, notificador, u["docente2"], mundo, "d")       # docente2 → alumno de 1H
    listar = ListarReportes(uow)
    estudiantes = lambda actor: {r.numero_control[-1] for r in listar.ejecutar(actor)}  # noqa: E731

    assert estudiantes(u["orientacion"]) == {"1", "4"}               # ven todo
    assert estudiantes(u["subdireccion"]) == {"1", "4"}
    assert estudiantes(u["docente"]) == {"1"}                         # solo lo que creó
    assert estudiantes(u["docente2"]) == {"4"}
    assert estudiantes(u["tutor"]) == {"1"}                           # estudiantes de su grupo (1G), aunque otro creó el reporte
    with pytest.raises(PermisoDenegado):
        listar.ejecutar(u["prefecto"])                                # los prefectos solo generan


def test_el_tutor_ve_el_historial_de_su_grupo_pero_no_de_otros(uow, reloj, notificador, mundo):
    u = mundo["u"]
    r_a = _crear(uow, reloj, notificador, u["prefecto"], mundo, "a")[0].reporte_id
    r_d = _crear(uow, reloj, notificador, u["prefecto"], mundo, "d")[0].reporte_id
    assert ObtenerReporte(uow).ejecutar(u["tutor"], r_a).listado.estudiante.startswith("Alvarez")
    with pytest.raises(PermisoDenegado):
        ObtenerReporte(uow).ejecutar(u["tutor"], r_d)
    with pytest.raises(PermisoDenegado):
        ObtenerReporte(uow).ejecutar(u["docente2"], r_a)
    with pytest.raises(NoEncontrado):
        ObtenerReporte(uow).ejecutar(u["orientacion"], 9999)


def test_los_reportes_relacionados_solo_muestran_lo_que_el_usuario_puede_ver(uow, reloj, notificador, mundo):
    u = mundo["u"]
    creados = _crear(uow, reloj, notificador, u["docente"], mundo, "ad")  # pelea entre alumno de 1G y de 1H
    id_a = next(c.reporte_id for c in creados if c.estudiante_id == mundo["est"]["a"].id)
    por_orientacion = ObtenerReporte(uow).ejecutar(u["orientacion"], id_a)
    assert len(por_orientacion.relacionados) == 1
    por_tutor = ObtenerReporte(uow).ejecutar(u["tutor"], id_a)       # tutor de 1G: no ve al estudiante de 1H
    assert por_tutor.relacionados == []


def test_filtros_del_listado(uow, reloj, notificador, mundo):
    u = mundo["u"]
    _crear(uow, reloj, notificador, u["docente"], mundo, "a", G.LEVE)
    graves = _crear(uow, reloj, notificador, u["docente"], mundo, "b", G.GRAVE, fecha_hora_incidente=datetime(2026, 9, 1, 8, 0))
    _crear(uow, reloj, notificador, u["docente"], mundo, "d", G.MEDIA)
    listar = lambda **f: ListarReportes(uow).ejecutar(u["orientacion"], **f)  # noqa: E731
    assert len(listar(gravedad=G.GRAVE)) == 1
    assert len(listar(grupo_id=mundo["grupos"]["1H"].id)) == 1
    assert len(listar(carrera_id=mundo["carrera"].id)) == 3
    assert [r.reporte.folio for r in listar(texto=graves[0].folio.lower())] == [graves[0].folio]
    assert len(listar(texto="beltrán")) == 1 and len(listar(texto="inexistente")) == 0
    assert len(listar(desde=datetime(2026, 10, 1, tzinfo=timezone.utc))) == 2
    assert [r.reporte.estudiante_id for r in listar(estudiante_id=mundo["est"]["a"].id)] == [mundo["est"]["a"].id]
    assert listar(estado=EstadoReporte.ATENDIDO_SUBDIRECCION) == []


# ---------- gestión ----------
def test_corregir_deja_historial_por_campo_y_rechaza_sin_cambios(uow, reloj, notificador, mundo):
    rid = _crear(uow, reloj, notificador, mundo["u"]["docente"], mundo, "a")[0].reporte_id
    oid = mundo["u"]["orientacion"].id
    CorregirReporte(uow, reloj).ejecutar(
        oid, rid, comentario="Aclaración con el docente", descripcion="Se agredió a un compañero en el receso.",
        tipo_incidencia_id=mundo["otro"].id, descripcion_otro="Agresión verbal")
    r = uow.reportes.obtener_por_id(rid)
    assert (r.tipo_incidencia_id, r.descripcion_otro) == (mundo["otro"].id, "Agresión verbal")
    cambios = {(c, a, n) for t, c, a, n in _historial(uow, rid) if t == TipoEventoReporte.CORRECCION}
    assert ("tipo_incidencia_id", "Pelea", "Otro") in cambios and ("descripcion_otro", None, "Agresión verbal") in cambios
    with pytest.raises(ReglaDeNegocioViolada):
        CorregirReporte(uow, reloj).ejecutar(oid, rid, descripcion=r.descripcion)  # sin cambios reales
    with pytest.raises(ReglaDeNegocioViolada):
        CorregirReporte(uow, reloj).ejecutar(oid, rid, tipo_incidencia_id=mundo["otro"].id, descripcion_otro=None)
    with pytest.raises(ReglaDeNegocioViolada):
        CorregirReporte(uow, reloj).ejecutar(oid, rid, estado="X")  # campo no corregible
    CorregirReporte(uow, reloj).ejecutar(oid, rid, tipo_incidencia_id=mundo["pelea"].id)  # al salir de 'Otro' se limpia
    assert uow.reportes.obtener_por_id(rid).descripcion_otro is None


def test_cambiar_gravedad_alerta_solo_al_escalar(uow, reloj, notificador, mundo):
    rid = _crear(uow, reloj, notificador, mundo["u"]["docente"], mundo, "a", G.LEVE)[0].reporte_id
    oid = mundo["u"]["orientacion"].id
    caso = CambiarGravedad(uow, reloj, notificador)
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(oid, rid, G.GRAVE, "")                        # motivo obligatorio
    caso.ejecutar(oid, rid, G.GRAVE, "Hubo lesiones")
    assert len(notificador.alertas) == 1
    caso.ejecutar(oid, rid, G.MUY_GRAVE, "Intervino la policía")     # ya estaba escalado: no repite
    caso.ejecutar(oid, rid, G.MEDIA, "Se aclaró el incidente")
    caso.ejecutar(oid, rid, G.GRAVE, "Nueva información")            # vuelve a escalar
    assert len(notificador.alertas) == 2
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(oid, rid, G.GRAVE, "Mismo valor")
    cambios = [(a, n) for t, c, a, n in _historial(uow, rid) if t == TipoEventoReporte.GRAVEDAD]
    assert cambios == [("LEVE", "GRAVE"), ("GRAVE", "MUY_GRAVE"), ("MUY_GRAVE", "MEDIA"), ("MEDIA", "GRAVE")]


def test_turnar_a_subdireccion_una_sola_vez(uow, reloj, notificador, mundo):
    rid = _crear(uow, reloj, notificador, mundo["u"]["docente"], mundo, "a")[0].reporte_id
    TurnarASubdireccion(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, "Ya se habló con los padres")
    assert uow.reportes.obtener_por_id(rid).estado == EstadoReporte.ATENDIDO_SUBDIRECCION
    assert _historial(uow, rid)[-1][2:] == ("EN_REVISION_ORIENTACION", "ATENDIDO_SUBDIRECCION")
    with pytest.raises(ReglaDeNegocioViolada):
        TurnarASubdireccion(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid)


def test_cancelar_no_borra_y_bloquea_cambios(uow, reloj, notificador, mundo):
    d, o = mundo["u"]["docente"], mundo["u"]["orientacion"]
    rid = _crear(uow, reloj, notificador, d, mundo, "a")[0].reporte_id
    with pytest.raises(ReglaDeNegocioViolada):
        CancelarReporte(uow, reloj).ejecutar(o.id, rid, "corto")
    CancelarReporte(uow, reloj).ejecutar(o.id, rid, "Se capturó en el estudiante equivocado")
    assert uow.reportes.obtener_por_id(rid).cancelado
    assert ListarReportes(uow).ejecutar(o) == []                                   # no aparece por defecto
    assert len(ListarReportes(uow).ejecutar(o, incluir_cancelados=True)) == 1      # pero sigue existiendo
    detalle = ObtenerReporte(uow).ejecutar(o, rid)
    assert detalle.cancelado_por_nombre == "Orientación" and detalle.listado.reporte.motivo_cancelacion
    with pytest.raises(ReglaDeNegocioViolada):
        CambiarGravedad(uow, reloj, notificador).ejecutar(o.id, rid, G.GRAVE, "Ya no debería poder")
    with pytest.raises(ReglaDeNegocioViolada):
        CancelarReporte(uow, reloj).ejecutar(o.id, rid, "Cancelar otra vez el mismo reporte")


# ---------- evidencias ----------
def _adjuntar(uow, almacen, reloj, actor, rid, contenido=PNG, nombre="foto.png", **kw):
    return AgregarAdjunto(uow, almacen, reloj).ejecutar(actor, rid, nombre, contenido, **kw)


def test_adjuntos_validan_el_contenido_real(uow, reloj, notificador, almacen, mundo):
    d = mundo["u"]["docente"]
    rid = _crear(uow, reloj, notificador, d, mundo, "a")[0].reporte_id
    assert _adjuntar(uow, almacen, reloj, d, rid)[0].tipo_mime == "image/png"
    assert _adjuntar(uow, almacen, reloj, d, rid, PDF, "acta.pdf")[0].tipo_mime == "application/pdf"
    for malo, nombre in [(b"#!/bin/sh\nrm -rf /", "foto.png"), (b"MZ\x90\x00", "doc.pdf"), (b"", "x.png"), (PNG + b"0" * (5 * 1024 * 1024), "grande.png")]:
        with pytest.raises(ReglaDeNegocioViolada):
            _adjuntar(uow, almacen, reloj, d, rid, malo, nombre)
    nombre_peligroso = _adjuntar(uow, almacen, reloj, d, rid, nombre="../../etc/passwd.png")[0].nombre_original
    assert nombre_peligroso == "passwd.png"


def test_maximo_de_evidencias_por_reporte(uow, reloj, notificador, almacen, mundo):
    d = mundo["u"]["docente"]
    rid = _crear(uow, reloj, notificador, d, mundo, "a")[0].reporte_id
    for _ in range(5):
        _adjuntar(uow, almacen, reloj, d, rid)
    with pytest.raises(ReglaDeNegocioViolada):
        _adjuntar(uow, almacen, reloj, d, rid)


def test_quien_puede_adjuntar_y_quien_puede_descargar(uow, reloj, notificador, almacen, mundo):
    u = mundo["u"]
    rid = _crear(uow, reloj, notificador, u["prefecto"], mundo, "a")[0].reporte_id
    adj = _adjuntar(uow, almacen, reloj, u["prefecto"], rid)[0]       # el autor, aunque no pueda consultar reportes
    with pytest.raises(PermisoDenegado):
        _adjuntar(uow, almacen, reloj, u["docente2"], rid)             # otro docente, no
    _adjuntar(uow, almacen, reloj, u["orientacion"], rid)              # Orientación sí
    assert ObtenerAdjunto(uow, almacen).ejecutar(u["tutor"], rid, adj.id)[1] == PNG   # el tutor del grupo puede verla
    with pytest.raises(PermisoDenegado):
        ObtenerAdjunto(uow, almacen).ejecutar(u["docente2"], rid, adj.id)
    with pytest.raises(PermisoDenegado):
        ObtenerAdjunto(uow, almacen).ejecutar(u["prefecto"], rid, adj.id)   # los prefectos no consultan
    TurnarASubdireccion(uow, reloj).ejecutar(u["orientacion"].id, rid)
    with pytest.raises(PermisoDenegado):
        _adjuntar(uow, almacen, reloj, u["prefecto"], rid)             # el autor ya no puede tras turnarse
    _adjuntar(uow, almacen, reloj, u["orientacion"], rid)              # Orientación sigue pudiendo


def test_adjuntar_a_todo_el_incidente_usa_una_sola_copia(uow, reloj, notificador, almacen, mundo):
    d = mundo["u"]["docente"]
    creados = _crear(uow, reloj, notificador, d, mundo, "abc")
    primero = creados[0].reporte_id
    adjuntos = _adjuntar(uow, almacen, reloj, d, primero, aplicar_a_incidente=True)
    assert len(adjuntos) == 3 and len(almacen.archivos) == 1
    assert all(len(uow.adjuntos.listar_por_reporte(c.reporte_id)) == 1 for c in creados)
    assert any(t == TipoEventoReporte.ADJUNTO for t, *_ in _historial(uow, creados[2].reporte_id))
    with pytest.raises(NoEncontrado):
        ObtenerAdjunto(uow, almacen).ejecutar(mundo["u"]["orientacion"], creados[1].reporte_id, adjuntos[0].id)  # pertenece a otro reporte
