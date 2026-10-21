import pytest

from app.application.use_cases.alertas.bandeja import ListarAlertas, MarcarAlertaAtendida
from app.application.use_cases.llamadas.registrar_llamada import RegistrarLlamada
from app.application.use_cases.reportes.consultas import ListarReportes, ObtenerReporte
from app.application.use_cases.reportes.crear_reportes import CrearReportes
from app.application.use_cases.reportes.gestion import CancelarReporte, TurnarASubdireccion
from app.application.use_cases.sanciones.aplicar_sanciones import AplicarSancionDirecta, AplicarSancionPorAcumulacion
from app.application.use_cases.sanciones.expediente import ObtenerExpediente
from app.domain.entities.tipo_sancion import TipoSancion
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_llamada import EstadoLlamada as L
from app.domain.value_objects.estado_reporte import EstadoReporte as E, TipoEventoReporte
from app.domain.value_objects.gravedad import Gravedad as G
from app.domain.value_objects.origen_sancion import OrigenSancion
from app.domain.value_objects.rol import Rol
from app.infrastructure.notifications.notificador_bandeja import NotificadorBandejaCorreo
from tests.unit.fakes import CorreoMem

TEXTO = "Se peleó con un compañero durante el receso."


class Mundo:
    """Atajos para escenarios de sanciones."""

    def __init__(self, uow, reloj, notificador, mundo):
        self.uow, self.reloj, self.n, self.m = uow, reloj, notificador, mundo
        self.sub = mundo["u"]["subdireccion"]
        self.orient = mundo["u"]["orientacion"]
        self.suspension = uow.tipos_sancion.guardar(TipoSancion(nombre="Suspensión de N días", requiere_dias=True))
        self.carta = uow.tipos_sancion.guardar(TipoSancion(nombre="Carta compromiso"))

    def reporte(self, letra="a", gravedad=G.LEVE, actor=None) -> int:
        self.reloj.avanzar(minutes=1)
        return CrearReportes(self.uow, self.reloj, self.n).ejecutar(
            actor or self.m["u"]["docente"], [self.m["est"][letra].id], self.m["pelea"].id, TEXTO, gravedad)[0].reporte_id

    def llamar(self, *reporte_ids):
        for rid in reporte_ids:
            RegistrarLlamada(self.uow, self.reloj).ejecutar(self.orient.id, rid, L.ATENDIDA, atendio_nombre="Madre")

    def directa(self, rid, tipo=None, **kw):
        return AplicarSancionDirecta(self.uow, self.reloj).ejecutar(self.sub.id, rid, (tipo or self.carta).id, **kw)

    def acumulacion(self, letra="a", tipo=None, **kw):
        return AplicarSancionPorAcumulacion(self.uow, self.reloj).ejecutar(
            self.sub.id, self.m["est"][letra].id, (tipo or self.carta).id, **kw)

    def reportes(self, rid):
        return self.uow.reportes.obtener_por_id(rid)


@pytest.fixture
def w(uow, reloj, notificador, mundo):
    return Mundo(uow, reloj, notificador, mundo)


# ---------- ciclos y alerta de acumulación ----------
def test_los_reportes_de_un_estudiante_comparten_ciclo_y_cada_estudiante_tiene_el_suyo(w, uow):
    a1, a2, b1 = w.reporte("a"), w.reporte("a"), w.reporte("b")
    assert w.reportes(a1).ciclo_id == w.reportes(a2).ciclo_id != w.reportes(b1).ciclo_id
    ciclo = uow.ciclos.obtener_abierto(w.m["est"]["a"].id)
    assert (ciclo.numero, ciclo.abierto) == (1, True)


def test_alerta_de_acumulacion_al_llegar_a_tres_reportes(w, notificador):
    w.reporte("a"); w.reporte("a")
    assert notificador.acumulaciones == []
    w.reporte("a")
    (alerta,) = notificador.acumulaciones
    assert (alerta.total, alerta.umbral, alerta.grupo) == (3, 3, "1G") and len(alerta.folios) == 3
    w.reporte("a")                                           # sigue pendiente de sanción: vuelve a avisar
    assert notificador.acumulaciones[-1].total == 4


def test_un_reporte_cancelado_no_cuenta(w, uow):
    ids = [w.reporte("a") for _ in range(3)]
    CancelarReporte(uow, w.reloj).ejecutar(w.orient.id, ids[0], "Estudiante equivocado al capturar")
    w.llamar(*ids[1:])
    with pytest.raises(ReglaDeNegocioViolada) as e:
        w.acumulacion()
    assert "2 de 3" in str(e.value)


# ---------- sanción directa ----------
def test_la_sancion_directa_solo_aplica_a_graves_y_muy_graves(w):
    leve = w.reporte("a", G.LEVE)
    w.llamar(leve)
    with pytest.raises(ReglaDeNegocioViolada) as e:
        w.directa(leve)
    assert "Grave o Muy grave" in str(e.value)
    assert w.reportes(leve).estado == E.EN_REVISION_ORIENTACION


def test_no_se_concluye_sin_llamada_realizada_o_atendida(w):
    rid = w.reporte("a", G.GRAVE)
    with pytest.raises(ReglaDeNegocioViolada) as e:
        w.directa(rid)
    assert "llamada" in str(e.value) and w.reportes(rid).folio in str(e.value)
    RegistrarLlamada(w.uow, w.reloj).ejecutar(w.orient.id, rid, L.NO_CONTESTO)
    with pytest.raises(ReglaDeNegocioViolada):               # 'No contestó' no basta
        w.directa(rid)
    w.llamar(rid)
    w.directa(rid)
    assert w.reportes(rid).estado == E.SANCIONADO_CONCLUIDO


def test_la_directa_concluye_el_reporte_y_deja_el_historial(w, uow):
    rid = w.reporte("a", G.MUY_GRAVE)
    w.llamar(rid)
    detalle = w.directa(rid, w.suspension, dias=3, observaciones="  Agresión con lesiones ")
    r = w.reportes(rid)
    assert (r.estado, r.cuenta_acumulacion, r.es_contable) == (E.SANCIONADO_CONCLUIDO, False, False)
    s = detalle.sancion
    assert (s.origen, s.dias, s.observaciones, detalle.folios) == (OrigenSancion.DIRECTA, 3, "Agresión con lesiones", [r.folio])
    estados = [(e.valor_anterior, e.valor_nuevo) for e in uow.historial_reportes.listar_por_reporte(rid) if e.tipo == TipoEventoReporte.ESTADO]
    assert estados == [("CREADO", "EN_REVISION_ORIENTACION"), ("EN_REVISION_ORIENTACION", "ATENDIDO_SUBDIRECCION"),
                       ("ATENDIDO_SUBDIRECCION", "SANCIONADO_CONCLUIDO")]          # pasó por Subdirección al sancionar
    assert any(e.tipo == TipoEventoReporte.SANCION and e.valor_nuevo == "Suspensión de N días (3 días)"
               for e in uow.historial_reportes.listar_por_reporte(rid))
    with pytest.raises(ReglaDeNegocioViolada):                # ya concluido: no se vuelve a sancionar
        w.directa(rid)


def test_validacion_de_tipo_y_dias(w):
    rid = w.reporte("a", G.GRAVE)
    w.llamar(rid)
    with pytest.raises(ReglaDeNegocioViolada):
        w.directa(rid, w.suspension)                           # requiere días
    with pytest.raises(ReglaDeNegocioViolada):
        w.directa(rid, w.suspension, dias=400)
    with pytest.raises(NoEncontrado):
        AplicarSancionDirecta(w.uow, w.reloj).ejecutar(w.sub.id, rid, 9999)
    w.carta.activo = False
    w.uow.tipos_sancion.guardar(w.carta)
    with pytest.raises(ReglaDeNegocioViolada):
        w.directa(rid, w.carta)
    assert w.directa(rid, w.suspension, dias=5).sancion.dias == 5
    # un tipo sin días ignora el valor recibido
    otro = w.reporte("b", G.GRAVE)
    w.llamar(otro)
    w.carta.activo = True
    w.uow.tipos_sancion.guardar(w.carta)
    assert w.directa(otro, w.carta, dias=7).sancion.dias is None


def test_la_sancion_directa_no_reinicia_el_ciclo_ni_cuenta_para_las_tres(w, uow, notificador):
    l1, l2, grave = w.reporte("a"), w.reporte("a"), w.reporte("a", G.GRAVE)   # 3 reportes: ya procede acumulación
    w.llamar(grave)
    w.directa(grave)                                                          # el Grave sale de la cuenta
    ciclo = uow.ciclos.obtener_abierto(w.m["est"]["a"].id)
    assert ciclo is not None and ciclo.numero == 1                            # el ciclo sigue abierto
    notificador.acumulaciones.clear()
    w.reporte("a")                                                            # 2 Leves + 1 nueva = 3 contables
    assert notificador.acumulaciones[0].total == 3
    assert w.reportes(grave).ciclo_id == ciclo.id and not w.reportes(grave).es_contable


def test_un_grave_sin_sancion_directa_si_cuenta(w):
    ids = [w.reporte("a"), w.reporte("a"), w.reporte("a", G.GRAVE)]
    w.llamar(*ids)
    detalle = w.acumulacion(tipo=w.carta)                                     # 2 Leves + 1 Grave = 3
    assert len(detalle.folios) == 3


# ---------- sanción por acumulación ----------
def test_la_sancion_por_acumulacion_cubre_el_ciclo_y_reinicia_el_contador(w, uow):
    a1, a2, a3 = w.reporte("a"), w.reporte("a", G.MEDIA), w.reporte("a")
    cancelado, otro_estudiante = w.reporte("a"), w.reporte("b")
    CancelarReporte(uow, w.reloj).ejecutar(w.orient.id, cancelado, "Estudiante equivocado al capturar")
    TurnarASubdireccion(uow, w.reloj).ejecutar(w.orient.id, a1)               # a1 ya estaba en Subdirección
    w.llamar(a1, a2, a3)

    detalle = w.acumulacion(tipo=w.suspension, dias=2, observaciones="Acumulación de faltas")
    assert detalle.sancion.origen == OrigenSancion.ACUMULACION and detalle.sancion.dias == 2
    assert detalle.folios == sorted(w.reportes(r).folio for r in (a1, a2, a3))
    assert all(w.reportes(r).estado == E.SANCIONADO_CONCLUIDO for r in (a1, a2, a3))
    assert w.reportes(cancelado).estado == E.EN_REVISION_ORIENTACION and w.reportes(cancelado).cancelado
    assert w.reportes(otro_estudiante).estado == E.EN_REVISION_ORIENTACION   # otros estudiantes, intactos
    assert uow.ciclos.obtener_abierto(w.m["est"]["a"].id) is None             # ciclo cerrado
    assert uow.ciclos.listar_por_estudiante(w.m["est"]["a"].id)[0].fecha_cierre is not None
    assert len([e for e in uow.historial_reportes.listar_por_reporte(a2) if e.tipo == TipoEventoReporte.SANCION]) == 1

    nuevo = w.reporte("a")                                                    # el contador vuelve a cero
    assert uow.ciclos.obtener_abierto(w.m["est"]["a"].id).numero == 2
    assert w.reportes(nuevo).ciclo_id != w.reportes(a1).ciclo_id
    with pytest.raises(ReglaDeNegocioViolada):
        w.acumulacion()                                                       # 1 de 3 en el ciclo nuevo


def test_acumulacion_requiere_llamada_en_todos_los_reportes_y_es_atomica(w, uow):
    ids = [w.reporte("a") for _ in range(3)]
    w.llamar(ids[0], ids[1])                                                  # falta el tercero
    with pytest.raises(ReglaDeNegocioViolada) as e:
        w.acumulacion()
    assert w.reportes(ids[2]).folio in str(e.value)
    assert all(w.reportes(r).estado == E.EN_REVISION_ORIENTACION for r in ids)
    assert uow.ciclos.obtener_abierto(w.m["est"]["a"].id) is not None
    assert uow.sanciones.listar_por_estudiante(w.m["est"]["a"].id) == []


def test_acumulacion_sin_reportes_o_estudiante_inexistente(w):
    with pytest.raises(ReglaDeNegocioViolada):
        w.acumulacion("c")                                                    # sin reportes
    with pytest.raises(NoEncontrado):
        AplicarSancionPorAcumulacion(w.uow, w.reloj).ejecutar(w.sub.id, 9999, w.carta.id)


# ---------- consultas ----------
def test_expediente_con_ciclos_y_sanciones_directas(w, uow):
    ids = [w.reporte("a") for _ in range(3)]
    w.llamar(*ids)
    w.acumulacion(tipo=w.carta)                                               # cierra el ciclo 1
    grave = w.reporte("a", G.GRAVE)
    w.llamar(grave)
    w.directa(grave, w.suspension, dias=1)
    cancelado = w.reporte("a")
    CancelarReporte(uow, w.reloj).ejecutar(w.orient.id, cancelado, "Estudiante equivocado al capturar")
    w.reporte("a")

    e = ObtenerExpediente(uow).ejecutar(w.m["est"]["a"].id)
    assert (e.total_reportes, e.umbral, e.grupo_actual) == (5, 3, "1G")       # el cancelado no se cuenta
    assert [c.ciclo.numero for c in e.ciclos_anteriores] == [1]
    assert e.ciclos_anteriores[0].sancion.sancion.origen == OrigenSancion.ACUMULACION and len(e.ciclos_anteriores[0].reportes) == 3
    assert e.ciclo_actual.ciclo.numero == 2 and e.ciclo_actual.contables == 1 and len(e.ciclo_actual.reportes) == 3
    assert [s.sancion.dias for s in e.sanciones_directas] == [1]
    with pytest.raises(NoEncontrado):
        ObtenerExpediente(uow).ejecutar(9999)


def test_el_detalle_muestra_la_sancion_y_la_acumulacion_segun_el_rol(w, uow):
    u = w.m["u"]
    rid = w.reporte("a", G.GRAVE, actor=u["docente"])
    w.llamar(rid)
    w.directa(rid, w.suspension, dias=3, observaciones="Detalle reservado")
    w.reporte("a")

    por_docente = ObtenerReporte(uow).ejecutar(u["docente"], rid)             # el autor
    assert (por_docente.sancion.tipo_nombre, por_docente.sancion.sancion.dias) == ("Suspensión de N días", 3)
    assert por_docente.sancion.sancion.observaciones is None and por_docente.acumulacion is None
    por_sub = ObtenerReporte(uow).ejecutar(u["subdireccion"], rid)
    assert por_sub.sancion.sancion.observaciones == "Detalle reservado"
    assert (por_sub.acumulacion.total, por_sub.acumulacion.umbral) == (1, 3)  # el Grave sancionado no cuenta


def test_el_reporte_cubierto_por_acumulacion_muestra_la_sancion_del_ciclo(w, uow):
    ids = [w.reporte("a") for _ in range(3)]
    w.llamar(*ids)
    w.acumulacion(tipo=w.suspension, dias=4)
    d = ObtenerReporte(uow).ejecutar(w.sub, ids[1])
    assert d.sancion.sancion.origen == OrigenSancion.ACUMULACION and len(d.sancion.folios) == 3
    assert len(ListarReportes(uow).ejecutar(w.sub, estado=E.SANCIONADO_CONCLUIDO)) == 3


# ---------- bandeja de alertas y correo ----------
def _notificador(uow, reloj, correo):
    return NotificadorBandejaCorreo(lambda: uow, correo, reloj, "http://app.test/", "CBTis 147")


def test_alertas_en_la_bandeja_y_por_correo_a_subdireccion(uow, reloj, mundo):
    correo = CorreoMem()
    n = _notificador(uow, reloj, correo)
    CrearReportes(uow, reloj, n).ejecutar(mundo["u"]["docente"], [mundo["est"]["a"].id], mundo["pelea"].id, TEXTO, G.MUY_GRAVE)

    (alerta,) = ListarAlertas(uow).ejecutar().notificaciones
    assert alerta.tipo == "REPORTE_GRAVE" and "Muy grave" in alerta.titulo and alerta.correo_enviado and alerta.correo_error is None
    destinatarios, asunto, cuerpo = correo.enviados[0]
    assert destinatarios == ["sub@cbtis.mx"] and "CBTis 147" in asunto
    assert f"http://app.test/reportes/{alerta.reporte_id}" in cuerpo and "receso" not in cuerpo   # sin los hechos


def test_alerta_de_acumulacion_apunta_al_expediente(uow, reloj, mundo, notificador):
    correo = CorreoMem()
    n = _notificador(uow, reloj, correo)
    for _ in range(3):
        CrearReportes(uow, reloj, n).ejecutar(mundo["u"]["docente"], [mundo["est"]["b"].id], mundo["pelea"].id, TEXTO, G.LEVE)
    alertas = ListarAlertas(uow).ejecutar().notificaciones
    assert [a.tipo for a in alertas] == ["ACUMULACION"]
    assert "acumula 3 reportes" in alertas[0].titulo and f"/estudiantes/{mundo['est']['b'].id}/expediente" in correo.enviados[0][2]


def test_si_falla_el_correo_la_alerta_queda_en_la_bandeja(uow, reloj, mundo):
    correo = CorreoMem()
    correo.falla = "Connection refused"
    CrearReportes(uow, reloj, _notificador(uow, reloj, correo)).ejecutar(
        mundo["u"]["docente"], [mundo["est"]["a"].id], mundo["pelea"].id, TEXTO, G.GRAVE)
    (a,) = ListarAlertas(uow).ejecutar().notificaciones
    assert not a.correo_enviado and a.correo_error == "Connection refused"


def test_marcar_alertas_como_atendidas(uow, reloj, mundo):
    n = _notificador(uow, reloj, CorreoMem())
    CrearReportes(uow, reloj, n).ejecutar(mundo["u"]["docente"], [mundo["est"]["a"].id, mundo["est"]["b"].id], mundo["pelea"].id, TEXTO, G.GRAVE)
    pagina = ListarAlertas(uow).ejecutar()
    assert pagina.pendientes == 2
    sub = mundo["u"]["subdireccion"]
    MarcarAlertaAtendida(uow, reloj).ejecutar(sub.id, pagina.notificaciones[0].id)
    MarcarAlertaAtendida(uow, reloj).ejecutar(mundo["u"]["orientacion"].id, pagina.notificaciones[0].id)  # idempotente
    assert ListarAlertas(uow).ejecutar().pendientes == 1 and len(ListarAlertas(uow).ejecutar(solo_pendientes=False).notificaciones) == 2
    assert uow.notificaciones.obtener_por_id(pagina.notificaciones[0].id).atendida_por == sub.id
    with pytest.raises(NoEncontrado):
        MarcarAlertaAtendida(uow, reloj).ejecutar(sub.id, 9999)


def test_permisos_de_sanciones_y_alertas():
    def roles(p):
        return {r for r in Rol if tiene_permiso([r], p)}
    assert roles(Permiso.APLICAR_SANCIONES) == {Rol.SUBDIRECCION, Rol.DIRECCION}
    assert roles(Permiso.VER_ALERTAS) == {Rol.SUBDIRECCION, Rol.DIRECCION}
