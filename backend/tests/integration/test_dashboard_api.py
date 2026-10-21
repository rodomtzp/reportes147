from tests.integration.test_reportes_api import _cuerpo, ctx  # noqa: F401  (ctx es una fixture)

BASE = "/api/v1"


def test_dashboard_por_rol(client, ctx, headers_de):
    docente, orient, sub, prefecto = headers_de("DOCENTE"), headers_de("ORIENTACION"), headers_de("SUBDIRECCION"), headers_de("PREFECTO")
    for letras, gravedad in (("a", "LEVE"), ("b", "MUY_GRAVE"), ("d", "LEVE")):
        assert client.post(f"{BASE}/reportes", headers=docente, json=_cuerpo(ctx, letras, gravedad=gravedad)).status_code == 201

    d = client.get(f"{BASE}/dashboard", headers=orient).get_json()
    assert d["alcance"] == "total" and d["total_rango"] == 3 and d["rango"] == "periodo"
    assert {g["etiqueta"]: g["valor"] for g in d["por_gravedad"]} == {"Leve": 2, "Media": 0, "Grave": 0, "Muy grave": 1}
    assert d["pendientes_llamada"] == 3 and d["alertas_pendientes"] is None
    assert sum(p["valor"] for p in d["serie"]) == 3
    assert {g["etiqueta"] for g in d["por_grupo"]} == {"1G", "1H"}

    assert client.get(f"{BASE}/dashboard", headers=sub).get_json()["alertas_pendientes"] == 1   # el Muy grave
    propio = client.get(f"{BASE}/dashboard?rango=mes", headers=docente).get_json()
    assert propio["alcance"] == "propio" and propio["total_rango"] == 3 and propio["pendientes_llamada"] is None
    assert client.get(f"{BASE}/dashboard", headers=prefecto).get_json()["alcance"] == "ninguno"
    assert client.get(f"{BASE}/dashboard", headers=ctx["admin"]).get_json()["alcance"] == "ninguno"


def test_dashboard_valida_rango_y_exige_sesion(client, headers_de):
    assert client.get(f"{BASE}/dashboard").status_code == 401
    assert client.get(f"{BASE}/dashboard?rango=siempre", headers=headers_de("ORIENTACION")).status_code == 422
