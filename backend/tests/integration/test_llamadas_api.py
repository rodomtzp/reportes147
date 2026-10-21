from urllib.parse import parse_qs, unquote, urlparse

from tests.integration.test_reportes_api import _cuerpo, ctx  # noqa: F401  (ctx es una fixture)

BASE = "/api/v1"


def _crear(client, h, ctx, letras="a"):
    return client.post(f"{BASE}/reportes", headers=h, json=_cuerpo(ctx, letras)).get_json()[0]["id"]


def test_solo_orientacion_registra_llamadas(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = _crear(client, docente, ctx)
    for rol in ("DOCENTE", "PREFECTO", "SUBDIRECCION", "DIRECCION", "ADMINISTRADOR"):
        h = headers_de(rol)
        assert client.get(f"{BASE}/reportes/{rid}/llamadas", headers=h).status_code == 403
        assert client.post(f"{BASE}/reportes/{rid}/llamadas", headers=h, json={"estado": "REALIZADA"}).status_code == 403
        assert client.post(f"{BASE}/reportes/{rid}/whatsapp", headers=h, json={}).status_code == 403
    seg = client.get(f"{BASE}/reportes/{rid}/llamadas", headers=orient).get_json()
    assert seg["estado_llamada"] == "PENDIENTE" and seg["tutores"][0]["telefono"] == "4497654321"
    assert [l["estado"] for l in seg["llamadas"]] == ["PENDIENTE"]


def test_registro_de_resultados_y_reintentos(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = _crear(client, docente, ctx)
    url = f"{BASE}/reportes/{rid}/llamadas"
    assert client.post(url, headers=orient, json={"estado": "PENDIENTE"}).status_code == 422
    assert client.post(url, headers=orient, json={"estado": "TAL VEZ"}).status_code == 422
    assert client.post(url, headers=orient, json={"estado": "ATENDIDA"}).status_code == 422   # falta quién atendió

    r = client.post(url, headers=orient, json={"estado": "NO_CONTESTO", "observaciones": "Buzón de voz"})
    assert r.status_code == 201 and r.get_json()["estado_llamada"] == "NO_CONTESTO"
    assert client.get(f"{BASE}/reportes?sin_llamada_efectiva=true", headers=orient).get_json()[0]["estado_llamada"] == "NO_CONTESTO"

    r = client.post(url, headers=orient, json={"estado": "ATENDIDA", "atendio_nombre": "Laura Gómez"})
    datos = r.get_json()
    assert datos["estado_llamada"] == "ATENDIDA" and [l["estado"] for l in datos["llamadas"]] == ["NO_CONTESTO", "ATENDIDA"]
    assert datos["llamadas"][1]["atendio_nombre"] == "Laura Gómez" and datos["llamadas"][1]["realizado_por"]
    assert client.get(f"{BASE}/reportes?sin_llamada_efectiva=true", headers=orient).get_json() == []
    historial = client.get(f"{BASE}/reportes/{rid}", headers=orient).get_json()["historial"]
    assert [e["tipo"] for e in historial].count("LLAMADA") == 2


def test_mensaje_de_whatsapp(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = _crear(client, docente, ctx)
    r = client.post(f"{BASE}/reportes/{rid}/whatsapp", headers=orient, json={})
    assert r.status_code == 201
    datos = r.get_json()
    url = urlparse(datos["enlace"])
    assert (url.scheme, url.netloc, url.path) == ("https", "wa.me", "/524497654321")
    assert unquote(parse_qs(url.query)["text"][0]) == datos["texto"]
    assert "RPT-" in datos["texto"] and "Pelea" in datos["texto"] and "Orientación Educativa" in datos["texto"]
    assert "peleó" not in datos["texto"]                                   # no se detallan los hechos

    enviado = client.post(f"{BASE}/mensajes-whatsapp/{datos['id']}/enviado", headers=orient)
    assert enviado.status_code == 200 and enviado.get_json()["enviado_en"]
    assert client.post(f"{BASE}/mensajes-whatsapp/{datos['id']}/enviado", headers=docente).status_code == 403
    assert client.post(f"{BASE}/mensajes-whatsapp/9999/enviado", headers=orient).status_code == 404
    assert client.post(f"{BASE}/reportes/{rid}/whatsapp", headers=orient, json={"tutor_legal_id": 99999}).status_code == 422
    assert len(client.get(f"{BASE}/reportes/{rid}/llamadas", headers=orient).get_json()["mensajes"]) == 1


def test_el_detalle_expone_las_llamadas_solo_a_quien_ve_datos_de_contacto(client, ctx, headers_de):
    docente, orient, sub = headers_de("DOCENTE"), headers_de("ORIENTACION"), headers_de("SUBDIRECCION")
    rid = _crear(client, docente, ctx)
    client.post(f"{BASE}/reportes/{rid}/llamadas", headers=orient, json={"estado": "REALIZADA"})
    por_sub = client.get(f"{BASE}/reportes/{rid}", headers=sub).get_json()
    assert [l["estado"] for l in por_sub["llamadas"]] == ["REALIZADA"] and "telefono" not in str(por_sub["llamadas"])
    por_docente = client.get(f"{BASE}/reportes/{rid}", headers=docente).get_json()
    assert por_docente["llamadas"] is None and por_docente["mensajes_whatsapp"] is None
    assert por_docente["estado_llamada"] == "REALIZADA"


def test_no_se_elimina_un_tutor_con_llamadas_registradas(client, ctx, headers_de):
    docente, orient = headers_de("DOCENTE"), headers_de("ORIENTACION")
    rid = _crear(client, docente, ctx)
    client.post(f"{BASE}/reportes/{rid}/llamadas", headers=orient, json={"estado": "REALIZADA"})
    est = ctx["est"]["a"]
    nuevo = client.post(f"{BASE}/estudiantes/{est}/tutores-legales", headers=orient,
                        json={"nombre": "Pedro Pérez", "telefono": "4491112233"}).get_json()
    laura = next(t for t in nuevo if t["nombre"] == "Laura Gómez")
    assert client.delete(f"{BASE}/tutores-legales/{laura['id']}", headers=orient).status_code == 422
