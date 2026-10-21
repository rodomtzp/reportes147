from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from app.application.use_cases.estudiantes.crear_estudiante import CrearEstudiante  # noqa: F401
from app.application.use_cases.estudiantes.tutores_legales import AgregarTutorLegal, EliminarTutorLegal
from app.application.use_cases.llamadas.mensajes import GenerarMensajeWhatsApp, MarcarMensajeEnviado
from app.application.use_cases.llamadas.plantilla_mensaje import construir_mensaje_whatsapp
from app.application.use_cases.llamadas.registrar_llamada import RegistrarLlamada
from app.application.use_cases.llamadas.seguimiento import ObtenerSeguimientoLlamadas
from app.application.use_cases.reportes.consultas import ListarReportes, ObtenerReporte
from app.application.use_cases.reportes.crear_reportes import CrearReportes
from app.application.use_cases.reportes.gestion import CancelarReporte
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_llamadas import resumen_estado_llamada, tiene_llamada_efectiva
from app.domain.value_objects.estado_llamada import EstadoLlamada as L
from app.domain.value_objects.estado_reporte import TipoEventoReporte
from app.domain.value_objects.gravedad import Gravedad as G
from app.infrastructure.messaging.whatsapp_enlace import MensajeriaEnlaceManual

TEXTO = "Se peleó con un compañero durante el receso."


def _reporte(uow, reloj, notificador, mundo, letra="a", gravedad=G.LEVE):
    return CrearReportes(uow, reloj, notificador).ejecutar(
        mundo["u"]["docente"], [mundo["est"][letra].id], mundo["pelea"].id, TEXTO, gravedad)[0]


# ---------- política ----------
@pytest.mark.parametrize("estados,resumen,efectiva", [
    ([], L.PENDIENTE, False),
    ([L.PENDIENTE], L.PENDIENTE, False),
    ([L.NO_CONTESTO], L.NO_CONTESTO, False),
    ([L.NO_CONTESTO, L.PENDIENTE], L.PENDIENTE, False),
    ([L.NO_CONTESTO, L.REALIZADA], L.REALIZADA, True),
    ([L.REALIZADA, L.ATENDIDA], L.ATENDIDA, True),
])
def test_resumen_y_llamada_efectiva(estados, resumen, efectiva):
    assert resumen_estado_llamada(estados) == resumen
    assert tiene_llamada_efectiva(estados) is efectiva


# ---------- creación del reporte ----------
def test_cada_reporte_genera_una_llamada_pendiente_al_tutor_principal(uow, reloj, notificador, mundo):
    nuevo = AgregarTutorLegal(uow).ejecutar(mundo["est"]["a"].id, nombre="Pedro Pérez", telefono="4491112233")
    principal = next(t for t in nuevo if t.es_principal)
    creados = CrearReportes(uow, reloj, notificador).ejecutar(
        mundo["u"]["docente"], [mundo["est"]["a"].id, mundo["est"]["b"].id], mundo["pelea"].id, TEXTO, G.LEVE)
    for c in creados:  # un reporte = una llamada pendiente, aunque sean del mismo incidente
        intentos = uow.llamadas.listar_por_reporte(c.reporte_id)
        assert [(i.estado, i.realizado_por) for i in intentos] == [(L.PENDIENTE, None)]
    assert uow.llamadas.listar_por_reporte(creados[0].reporte_id)[0].tutor_legal_id == principal.id
    assert all(r.estado_llamada == "PENDIENTE" for r in ListarReportes(uow).ejecutar(mundo["u"]["orientacion"]))


# ---------- registro de resultados ----------
def test_el_resultado_completa_el_pendiente_y_los_reintentos_agregan_intentos(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    o = mundo["u"]["orientacion"].id
    caso = RegistrarLlamada(uow, reloj)

    caso.ejecutar(o, rid, L.NO_CONTESTO, observaciones="Buzón de voz")
    intentos = uow.llamadas.listar_por_reporte(rid)
    assert [(i.estado, i.realizado_por) for i in intentos] == [(L.NO_CONTESTO, o)]    # no se duplicó
    assert resumen_estado_llamada([i.estado for i in intentos]) == L.NO_CONTESTO

    reloj.avanzar(hours=3)
    caso.ejecutar(o, rid, L.ATENDIDA, atendio_nombre="  Laura   Gómez ")
    intentos = uow.llamadas.listar_por_reporte(rid)
    assert [i.estado for i in intentos] == [L.NO_CONTESTO, L.ATENDIDA]                 # nuevo intento
    assert intentos[1].atendio_nombre == "Laura Gómez" and intentos[1].fecha_hora == reloj.ahora()
    assert ListarReportes(uow).ejecutar(mundo["u"]["orientacion"])[0].estado_llamada == "ATENDIDA"

    eventos = [(e.tipo, e.campo, e.valor_nuevo, e.comentario) for e in uow.historial_reportes.listar_por_reporte(rid)
               if e.tipo == TipoEventoReporte.LLAMADA]
    assert eventos == [(TipoEventoReporte.LLAMADA, "Laura Gómez", "No contestó", "Buzón de voz"),
                       (TipoEventoReporte.LLAMADA, "Laura Gómez", "Atendida", "Atendió: Laura Gómez")]


def test_se_puede_llamar_a_otro_padre_o_tutor(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    otro = next(t for t in AgregarTutorLegal(uow).ejecutar(mundo["est"]["a"].id, nombre="Pedro Pérez", telefono="4491112233")
                if t.nombre == "Pedro Pérez")
    RegistrarLlamada(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, L.REALIZADA, tutor_legal_id=otro.id)
    assert uow.llamadas.listar_por_reporte(rid)[0].tutor_legal_id == otro.id
    # un tutor de otro estudiante no es válido
    ajeno = uow.tutores_legales.listar_por_estudiante(mundo["est"]["b"].id)[0]
    with pytest.raises(ReglaDeNegocioViolada):
        RegistrarLlamada(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, L.REALIZADA, tutor_legal_id=ajeno.id)


def test_validaciones_al_registrar(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    o, caso = mundo["u"]["orientacion"].id, RegistrarLlamada(uow, reloj)
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(o, rid, L.ATENDIDA)                                  # falta quién atendió
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(o, rid, L.PENDIENTE)                                 # el resultado no puede ser 'pendiente'
    with pytest.raises(ReglaDeNegocioViolada):
        caso.ejecutar(o, rid, L.REALIZADA, fecha_hora=reloj.ahora() + timedelta(hours=2))
    with pytest.raises(NoEncontrado):
        caso.ejecutar(o, 9999, L.REALIZADA)
    # los datos inválidos no dejaron nada a medias: el intento sigue pendiente
    assert [i.estado for i in uow.llamadas.listar_por_reporte(rid)] == [L.PENDIENTE]
    caso.ejecutar(o, rid, L.REALIZADA, atendio_nombre="se ignora", fecha_hora=datetime(2026, 10, 6, 8, 0))
    assert uow.llamadas.listar_por_reporte(rid)[0].atendio_nombre is None   # solo aplica a 'Atendida'


def test_no_se_registran_llamadas_en_un_reporte_cancelado(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    CancelarReporte(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, "Estudiante equivocado al capturar")
    with pytest.raises(ReglaDeNegocioViolada):
        RegistrarLlamada(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, L.REALIZADA)


def test_filtro_de_reportes_sin_llamada_efectiva(uow, reloj, notificador, mundo):
    a = _reporte(uow, reloj, notificador, mundo, "a").reporte_id
    b = _reporte(uow, reloj, notificador, mundo, "b").reporte_id
    c = _reporte(uow, reloj, notificador, mundo, "c").reporte_id
    o = mundo["u"]["orientacion"]
    RegistrarLlamada(uow, reloj).ejecutar(o.id, a, L.ATENDIDA, atendio_nombre="Madre")
    RegistrarLlamada(uow, reloj).ejecutar(o.id, b, L.NO_CONTESTO)
    pendientes = {r.reporte.id: r.estado_llamada for r in ListarReportes(uow).ejecutar(o, sin_llamada_efectiva=True)}
    assert pendientes == {b: "NO_CONTESTO", c: "PENDIENTE"}


# ---------- quién ve el seguimiento ----------
def test_el_detalle_solo_muestra_llamadas_a_quien_puede_ver_datos_de_contacto(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    RegistrarLlamada(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, L.ATENDIDA, atendio_nombre="Madre")
    por_subdireccion = ObtenerReporte(uow).ejecutar(mundo["u"]["subdireccion"], rid)
    assert [l.intento.estado for l in por_subdireccion.llamadas] == [L.ATENDIDA]
    por_docente = ObtenerReporte(uow).ejecutar(mundo["u"]["docente"], rid)       # autor del reporte
    assert por_docente.llamadas is None and por_docente.mensajes is None
    assert por_docente.listado.estado_llamada == "ATENDIDA"                       # solo el resumen


def test_seguimiento_de_orientacion_incluye_los_telefonos(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    seg = ObtenerSeguimientoLlamadas(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid)
    assert seg.estado_llamada == "PENDIENTE" and seg.tutores[0].telefono == "4497654321"
    assert [l.intento.estado for l in seg.llamadas] == [L.PENDIENTE]


# ---------- WhatsApp ----------
def _generador(uow, reloj, contacto=None):
    return GenerarMensajeWhatsApp(uow, reloj, MensajeriaEnlaceManual("52"), "CBTis 147", contacto)


def test_mensaje_formal_con_los_datos_necesarios_y_sin_detalles_sensibles(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo, gravedad=G.MUY_GRAVE).reporte_id
    g = _generador(uow, reloj, "Tel. 449 123 4567, de 8 a 15 h.").ejecutar(mundo["u"]["orientacion"].id, rid)
    t = g.mensaje.texto
    for esperado in ("Laura Gómez", "Alvarez Gómez Ana María", "(1G)", "RPT-2026-0001", "«Pelea»",
                     "6 de octubre de 2026", "comunicarse con Orientación Educativa", "Tel. 449 123 4567", "CBTis 147"):
        assert esperado in t
    assert "receso" not in t and "MUY" not in t.upper().replace("COMUNICARSE", "")  # ni los hechos ni la gravedad

    url = urlparse(g.enlace)
    assert (url.netloc, url.path) == ("wa.me", "/524497654321")
    assert unquote(parse_qs(url.query)["text"][0]) == t
    assert uow.mensajes_whatsapp.obtener_por_id(g.mensaje.id).enviado_en is None
    assert any(e.tipo == TipoEventoReporte.MENSAJE for e in uow.historial_reportes.listar_por_reporte(rid))


def test_el_mensaje_va_al_principal_o_al_tutor_elegido_y_se_marca_como_enviado(uow, reloj, notificador, mundo):
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id
    o = mundo["u"]["orientacion"].id
    otro = next(t for t in AgregarTutorLegal(uow).ejecutar(mundo["est"]["a"].id, nombre="Pedro Pérez", telefono="4491112233")
                if t.nombre == "Pedro Pérez")
    assert _generador(uow, reloj).ejecutar(o, rid).tutor.nombre == "Laura Gómez"
    g = _generador(uow, reloj).ejecutar(o, rid, otro.id)
    assert g.tutor.nombre == "Pedro Pérez" and "/524491112233" in g.enlace
    reloj.avanzar(minutes=5)
    assert MarcarMensajeEnviado(uow, reloj).ejecutar(o, g.mensaje.id).enviado_en == reloj.ahora()
    reloj.avanzar(minutes=5)
    assert MarcarMensajeEnviado(uow, reloj).ejecutar(o, g.mensaje.id).enviado_en != reloj.ahora()  # no se sobrescribe
    with pytest.raises(NoEncontrado):
        MarcarMensajeEnviado(uow, reloj).ejecutar(o, 9999)
    ajeno = uow.tutores_legales.listar_por_estudiante(mundo["est"]["b"].id)[0]
    with pytest.raises(ReglaDeNegocioViolada):
        _generador(uow, reloj).ejecutar(o, rid, ajeno.id)


def test_la_plantilla_para_otro_usa_la_descripcion_y_omite_el_grupo_si_no_hay():
    from datetime import timezone
    t = construir_mensaje_whatsapp("Ana", "Luis Pérez", None, "RPT-2026-0009", "Otro: Uso de celular",
                                   datetime(2027, 1, 1, tzinfo=timezone.utc), "CBTis 147")
    assert "Luis Pérez cuenta" in t and "«Otro: Uso de celular»" in t and "1 de enero de 2027" in t


# ---------- eliminar tutores con llamadas ----------
def test_no_se_elimina_un_tutor_con_llamadas_y_los_pendientes_pasan_al_principal(uow, reloj, notificador, mundo):
    est = mundo["est"]["a"].id
    otro = next(t for t in AgregarTutorLegal(uow).ejecutar(est, nombre="Pedro Pérez", telefono="4491112233")
                if t.nombre == "Pedro Pérez")
    principal = next(t for t in uow.tutores_legales.listar_por_estudiante(est) if t.es_principal)
    rid = _reporte(uow, reloj, notificador, mundo).reporte_id           # pendiente → principal (Laura)

    EliminarTutorLegal(uow).ejecutar(otro.id)                            # sin historial: se puede
    RegistrarLlamada(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, rid, L.NO_CONTESTO)
    nuevo = AgregarTutorLegal(uow).ejecutar(est, nombre="Tía Rosa", telefono="4493334455")
    with pytest.raises(ReglaDeNegocioViolada):                           # Laura ya tiene una llamada registrada
        EliminarTutorLegal(uow).ejecutar(principal.id)

    rid2 = _reporte(uow, reloj, notificador, mundo).reporte_id
    rosa = next(t for t in nuevo if t.nombre == "Tía Rosa")
    EliminarTutorLegal(uow).ejecutar(rosa.id)
    assert uow.llamadas.listar_por_reporte(rid2)[0].tutor_legal_id == principal.id
