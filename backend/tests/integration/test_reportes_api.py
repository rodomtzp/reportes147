import io

import pytest

from tests.integration.test_estudiantes_api import _estudiante, _preparar

BASE = "/api/v1"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
TEXTO = "Se peleó con un compañero durante el receso."


@pytest.fixture
def ctx(app, client, headers_de):
    """Mundo base: carrera, grupos, periodo vigente, 3 estudiantes y tipos de incidencia."""
    from app.domain.entities.tipo_incidencia import TipoIncidencia

    admin = headers_de("ADMINISTRADOR")
    base = _preparar(client, admin)
    ids = {}
    for n, grupo in (("a", "1G"), ("b", "1G"), ("d", "1H")):
        ids[n] = client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante(
            f"2430108015000{ord(n) - 96}", base["grupos"][grupo]["id"])).get_json()["id"]
    tipo = client.post(f"{BASE}/tipos-incidencia", headers=admin, json={"nombre": "Pelea"}).get_json()["id"]
    uow = app.extensions["container"].uow()
    with uow:
        otro = uow.tipos_incidencia.guardar(TipoIncidencia(nombre="Otro", es_otro=True)).id
        uow.commit()
    return {**base, "est": ids, "tipo": tipo, "otro": otro, "admin": admin}


def _cuerpo(ctx, letras="a", **extra):
    return {"estudiante_ids": [ctx["est"][l] for l in letras], "tipo_incidencia_id": ctx["tipo"],
            "descripcion": TEXTO, "gravedad": "LEVE", **extra}


def test_crear_reportes_devuelve_confirmacion_minima_y_folios_consecutivos(client, ctx, headers_de):
    prefecto = headers_de("PREFECTO")
    r = client.post(f"{BASE}/reportes", headers=prefecto, json=_cuerpo(ctx, "ab"))
    assert r.status_code == 201
    datos = r.get_json()
    assert [d["folio"].split("-")[2] for d in datos] == ["0001", "0002"]
    assert set(datos[0]) == {"id", "folio", "estudiante", "numero_control"}
    otro = client.post(f"{BASE}/reportes", headers=prefecto, json=_cuerpo(ctx, "d")).get_json()
    assert otro[0]["folio"].endswith("0003")
    assert client.get(f"{BASE}/reportes", headers=prefecto).status_code == 403   # el prefecto no consulta
    assert client.get(f"{BASE}/reportes/{datos[0]['id']}", headers=prefecto).status_code == 403
    assert client.post(f"{BASE}/reportes", headers=headers_de("ADMINISTRADOR"), json=_cuerpo(ctx)).status_code == 403


def test_validaciones_de_entrada(client, ctx, headers_de):
    docente = headers_de("DOCENTE")
    post = lambda **extra: client.post(f"{BASE}/reportes", headers=docente, json=_cuerpo(ctx, **extra))  # noqa: E731
    assert post(descripcion="corta").status_code == 422
    assert post(gravedad="ENORME").status_code == 422
    assert post(fecha_hora_incidente="2999-01-01T10:00:00").status_code == 422
    assert post(tipo_incidencia_id=ctx["otro"]).status_code == 422                       # 'Otro' sin descripción
    assert post(tipo_incidencia_id=ctx["otro"], descripcion_otro="Uso de celular").status_code == 201
    assert client.post(f"{BASE}/reportes", headers=docente, json={**_cuerpo(ctx), "estudiante_ids": []}).status_code == 422
    assert client.get(f"{BASE}/reportes?estado=INVENTADO", headers=headers_de("ORIENTACION")).status_code == 422
    assert client.get(f"{BASE}/reportes?desde=ayer", headers=headers_de("ORIENTACION")).status_code == 422


def test_visibilidad_por_rol(client, ctx, headers_de):
    docente, docente2, orient = headers_de("DOCENTE"), headers_de("DOCENTE"), headers_de("ORIENTACION")
    client.post(f"{BASE}/reportes", headers=docente, json=_cuerpo(ctx, "a"))
    client.post(f"{BASE}/reportes", headers=docente2, json=_cuerpo(ctx, "d"))
    ver = lambda h, q="": [r["numero_control"][-1] for r in client.get(f"{BASE}/reportes{q}", headers=h).get_json()]  # noqa: E731
    assert sorted(ver(orient)) == ["1", "4"] and ver(docente) == ["1"] and ver(docente2) == ["4"]
    assert ver(orient, "?q=Pérez&gravedad=LEVE&estado=EN_REVISION_ORIENTACION") != []
    assert ver(orient, "?gravedad=GRAVE") == []

    tutor = headers_de("DOCENTE")
    tutor_id = client.get(f"{BASE}/auth/me", headers=tutor).get_json()["id"]
    client.post(f"{BASE}/asignaciones-tutor", headers=ctx["admin"],
                json={"usuario_id": tutor_id, "grupo_id": ctx["grupos"]["1G"]["id"], "periodo_id": ctx["a"]["id"]})
    assert ver(tutor) == ["1"]   # estudiantes de su grupo, aunque el reporte lo creó otro docente


def test_flujo_de_gestion_con_historial(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = client.post(f"{BASE}/reportes", headers=docente, json=_cuerpo(ctx)).get_json()[0]["id"]

    assert client.patch(f"{BASE}/reportes/{rid}", headers=docente, json={"descripcion": "Texto distinto del original."}).status_code == 403
    r = client.patch(f"{BASE}/reportes/{rid}", headers=orient,
                     json={"descripcion": "Agredió físicamente a un compañero.", "comentario": "Aclarado con el docente"})
    assert r.status_code == 200 and r.get_json()["descripcion"].startswith("Agredió")
    assert client.patch(f"{BASE}/reportes/{rid}", headers=orient, json={"folio": "X"}).status_code == 422   # campo no editable

    g = client.post(f"{BASE}/reportes/{rid}/gravedad", headers=orient, json={"gravedad": "GRAVE", "motivo": "Hubo lesiones"})
    assert g.status_code == 200 and g.get_json()["gravedad"] == "GRAVE"
    assert client.post(f"{BASE}/reportes/{rid}/gravedad", headers=orient, json={"gravedad": "GRAVE", "motivo": "Igual"}).status_code == 422

    t = client.post(f"{BASE}/reportes/{rid}/turnar", headers=orient, json={"comentario": "Padres notificados"})
    assert t.status_code == 200 and t.get_json()["estado"] == "ATENDIDO_SUBDIRECCION"
    assert client.post(f"{BASE}/reportes/{rid}/turnar", headers=orient, json={}).status_code == 422

    detalle = client.get(f"{BASE}/reportes/{rid}", headers=orient).get_json()
    assert [e["tipo"] for e in detalle["historial"]] == ["CREACION", "ESTADO", "CORRECCION", "GRAVEDAD", "ESTADO"]
    assert detalle["historial"][3]["valor_anterior"] == "LEVE" and detalle["historial"][3]["usuario"]


def test_cancelar_un_reporte_lo_conserva_pero_oculta(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = client.post(f"{BASE}/reportes", headers=docente, json=_cuerpo(ctx)).get_json()[0]["id"]
    assert client.post(f"{BASE}/reportes/{rid}/cancelar", headers=docente, json={"motivo": "Motivo suficientemente largo"}).status_code == 403
    assert client.post(f"{BASE}/reportes/{rid}/cancelar", headers=orient, json={"motivo": "corto"}).status_code == 422
    c = client.post(f"{BASE}/reportes/{rid}/cancelar", headers=orient, json={"motivo": "Estudiante equivocado al capturar"})
    assert c.status_code == 200 and c.get_json()["cancelado"] is True
    assert client.get(f"{BASE}/reportes", headers=orient).get_json() == []
    assert len(client.get(f"{BASE}/reportes?incluir_cancelados=true", headers=orient).get_json()) == 1
    assert client.get(f"{BASE}/reportes/{rid}", headers=orient).get_json()["motivo_cancelacion"]


def test_evidencias_subida_y_descarga(client, ctx, headers_de):
    prefecto, docente2, orient = headers_de("PREFECTO"), headers_de("DOCENTE"), headers_de("ORIENTACION")
    ids = [c["id"] for c in client.post(f"{BASE}/reportes", headers=prefecto, json=_cuerpo(ctx, "ab")).get_json()]

    def subir(h, rid, contenido, nombre, **form):
        return client.post(f"{BASE}/reportes/{rid}/adjuntos", headers=h, content_type="multipart/form-data",
                           data={"archivo": (io.BytesIO(contenido), nombre), **form})

    assert subir(prefecto, ids[0], b"#!/bin/sh\necho hola", "foto.png").status_code == 422   # no es una imagen real
    assert subir(docente2, ids[0], PNG, "foto.png").status_code == 403
    r = subir(prefecto, ids[0], PNG, "evidencia.png", aplicar_a_incidente="true")
    assert r.status_code == 201 and len(r.get_json()) == 2                                     # a los dos reportes del incidente
    adjunto = client.get(f"{BASE}/reportes/{ids[1]}", headers=orient).get_json()["adjuntos"][0]
    assert adjunto["nombre"] == "evidencia.png"

    d = client.get(f"{BASE}/reportes/{ids[1]}/adjuntos/{adjunto['id']}", headers=orient)
    assert d.status_code == 200 and d.data == PNG and d.mimetype == "image/png"
    assert d.headers["X-Content-Type-Options"] == "nosniff" and "attachment" in d.headers["Content-Disposition"]
    assert client.get(f"{BASE}/reportes/{ids[1]}/adjuntos/{adjunto['id']}", headers=docente2).status_code == 403
    assert client.get(f"{BASE}/reportes/{ids[0]}/adjuntos/{adjunto['id']}", headers=orient).status_code == 404  # id de otro reporte
    assert client.post(f"{BASE}/reportes/{ids[0]}/adjuntos", headers=prefecto, content_type="multipart/form-data", data={}).status_code == 422
