from tests.integration.test_reportes_api import _cuerpo, ctx  # noqa: F401  (ctx es una fixture)

BASE = "/api/v1"


def _tipos(client, admin):
    susp = client.post(f"{BASE}/tipos-sancion", headers=admin, json={"nombre": "Suspensión de N días", "requiere_dias": True}).get_json()
    carta = client.post(f"{BASE}/tipos-sancion", headers=admin, json={"nombre": "Carta compromiso"}).get_json()
    return susp["id"], carta["id"]


def _reporte(client, h, ctx, letra="a", gravedad="LEVE"):
    return client.post(f"{BASE}/reportes", headers=h, json=_cuerpo(ctx, letra, gravedad=gravedad)).get_json()[0]["id"]


def _llamar(client, orient, rid):
    assert client.post(f"{BASE}/reportes/{rid}/llamadas", headers=orient,
                       json={"estado": "ATENDIDA", "atendio_nombre": "Madre"}).status_code == 201


def test_alertas_en_la_bandeja_de_subdireccion(client, ctx, headers_de):
    docente, sub, direccion = headers_de("DOCENTE"), headers_de("SUBDIRECCION"), headers_de("DIRECCION")
    _reporte(client, docente, ctx, "a", "LEVE")
    assert client.get(f"{BASE}/alertas/resumen", headers=sub).get_json() == {"pendientes": 0}   # un Leve no alerta
    rid = _reporte(client, docente, ctx, "b", "MUY_GRAVE")

    pagina = client.get(f"{BASE}/alertas", headers=sub).get_json()
    assert pagina["pendientes"] == 1
    a = pagina["alertas"][0]
    assert a["tipo"] == "REPORTE_GRAVE" and a["reporte_id"] == rid and "Muy grave" in a["titulo"]
    assert a["correo_enviado"] is False and a["correo_error"] == "SMTP no configurado"      # sin SMTP: queda en la bandeja

    for h in (docente, headers_de("ORIENTACION"), headers_de("ADMINISTRADOR")):
        assert client.get(f"{BASE}/alertas", headers=h).status_code == 403
    assert client.get(f"{BASE}/alertas", headers=direccion).status_code == 200            # Dirección también la ve
    assert client.post(f"{BASE}/alertas/{a['id']}/atendida", headers=sub).get_json()["atendida"] is True
    assert client.get(f"{BASE}/alertas/resumen", headers=sub).get_json() == {"pendientes": 0}
    assert client.get(f"{BASE}/alertas?pendientes=false", headers=sub).get_json()["alertas"][0]["atendida"] is True
    assert client.post(f"{BASE}/alertas/9999/atendida", headers=sub).status_code == 404


def test_sancion_directa_por_api(client, ctx, headers_de):
    docente, orient, sub = headers_de("DOCENTE"), headers_de("ORIENTACION"), headers_de("SUBDIRECCION")
    susp, carta = _tipos(client, ctx["admin"])
    leve, grave = _reporte(client, docente, ctx, "a", "LEVE"), _reporte(client, docente, ctx, "b", "GRAVE")

    url = f"{BASE}/reportes/{grave}/sancion"
    for h in (docente, orient, ctx["admin"]):
        assert client.post(url, headers=h, json={"tipo_sancion_id": carta}).status_code == 403
    assert client.post(url, headers=sub, json={"tipo_sancion_id": carta}).status_code == 422     # falta la llamada
    _llamar(client, orient, grave)
    assert client.post(url, headers=sub, json={"tipo_sancion_id": susp}).status_code == 422      # faltan los días
    assert client.post(url, headers=sub, json={"tipo_sancion_id": susp, "dias": 0}).status_code == 422
    r = client.post(url, headers=sub, json={"tipo_sancion_id": susp, "dias": 3, "observaciones": "Agresión"})
    assert r.status_code == 201
    d = r.get_json()
    assert d["estado"] == "SANCIONADO_CONCLUIDO" and d["sancion"]["origen"] == "DIRECTA" and d["sancion"]["dias"] == 3
    assert d["sancion"]["folios"] == [d["folio"]]
    assert d["acumulacion"]["total"] == 0                                                          # el Grave sancionado no cuenta
    assert client.post(url, headers=sub, json={"tipo_sancion_id": carta}).status_code == 422     # ya concluido

    _llamar(client, orient, leve)
    nope = client.post(f"{BASE}/reportes/{leve}/sancion", headers=sub, json={"tipo_sancion_id": carta})
    assert nope.status_code == 422 and "Grave o Muy grave" in nope.get_json()["error"]

    visto_por_docente = client.get(f"{BASE}/reportes/{grave}", headers=docente).get_json()
    assert visto_por_docente["sancion"]["tipo"] == "Suspensión de N días" and visto_por_docente["sancion"]["observaciones"] is None
    assert client.get(f"{BASE}/reportes/{grave}", headers=sub).get_json()["sancion"]["observaciones"] == "Agresión"


def test_sancion_por_acumulacion_y_expediente(client, ctx, headers_de):
    docente, orient, sub, direccion = headers_de("DOCENTE"), headers_de("ORIENTACION"), headers_de("SUBDIRECCION"), headers_de("DIRECCION")
    _, carta = _tipos(client, ctx["admin"])
    est = ctx["est"]["a"]
    ids = [_reporte(client, docente, ctx, "a") for _ in range(2)]
    url = f"{BASE}/estudiantes/{est}/sancion-acumulacion"

    assert client.post(url, headers=sub, json={"tipo_sancion_id": carta}).status_code == 422     # 2 de 3
    ids.append(_reporte(client, docente, ctx, "a"))
    alertas = client.get(f"{BASE}/alertas", headers=sub).get_json()["alertas"]
    assert any(a["tipo"] == "ACUMULACION" and a["estudiante_id"] == est for a in alertas)       # alerta al llegar a 3

    exp = client.get(f"{BASE}/estudiantes/{est}/expediente", headers=orient).get_json()
    assert exp["total_reportes"] == 3 and exp["ciclo_actual"]["contables"] == 3 and exp["ciclo_actual"]["listo_para_sancion"]
    assert client.get(f"{BASE}/estudiantes/{est}/expediente", headers=docente).status_code == 403
    assert client.post(url, headers=orient, json={"tipo_sancion_id": carta}).status_code == 403
    assert client.post(url, headers=direccion, json={"tipo_sancion_id": carta}).status_code == 422   # faltan llamadas
    for rid in ids:
        _llamar(client, orient, rid)

    r = client.post(url, headers=direccion, json={"tipo_sancion_id": carta, "observaciones": "Faltas reiteradas"})
    assert r.status_code == 201
    exp = r.get_json()
    assert exp["ciclo_actual"] is None and len(exp["ciclos_anteriores"]) == 1
    anterior = exp["ciclos_anteriores"][0]
    assert anterior["sancion"]["origen"] == "ACUMULACION" and len(anterior["sancion"]["folios"]) == 3
    assert all(rep["estado"] == "SANCIONADO_CONCLUIDO" for rep in anterior["reportes"])

    _reporte(client, docente, ctx, "a")                                                           # el contador vuelve a cero
    exp = client.get(f"{BASE}/estudiantes/{est}/expediente", headers=sub).get_json()
    assert exp["ciclo_actual"]["numero"] == 2 and exp["ciclo_actual"]["contables"] == 1
    assert client.post(url, headers=sub, json={"tipo_sancion_id": carta}).status_code == 422
    assert client.post(f"{BASE}/estudiantes/9999/sancion-acumulacion", headers=sub, json={"tipo_sancion_id": carta}).status_code == 404
    assert client.get(f"{BASE}/reportes/{ids[0]}", headers=sub).get_json()["sancion"]["origen"] == "ACUMULACION"
