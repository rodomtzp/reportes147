BASE = "/api/v1"


def test_solo_el_administrador_gestiona_usuarios(client, headers_de):
    for rol in ["DOCENTE", "PREFECTO", "ORIENTACION", "SUBDIRECCION", "DIRECCION"]:
        h = headers_de(rol)
        assert client.get(f"{BASE}/usuarios", headers=h).status_code == 403
        assert client.post(f"{BASE}/carreras", headers=h, json={"nombre": "X", "clave": "X"}).status_code == 403
    assert client.get(f"{BASE}/usuarios").status_code == 401


def test_alta_de_usuario_devuelve_password_temporal_una_sola_vez(client, headers_de, login):
    admin = headers_de("ADMINISTRADOR")
    r = client.post(f"{BASE}/usuarios", headers=admin,
                    json={"nombre": "Laura Pérez", "correo": "Laura@cbtis.mx", "roles": ["DOCENTE", "PREFECTO"]})
    assert r.status_code == 201
    datos = r.get_json()
    assert datos["usuario"]["correo"] == "laura@cbtis.mx"
    assert datos["usuario"]["debe_cambiar_password"] is True
    assert "password_hash" not in datos["usuario"]
    assert login("laura@cbtis.mx", datos["password_temporal"]).status_code == 200

    lista = client.get(f"{BASE}/usuarios?rol=DOCENTE", headers=admin).get_json()
    assert [u["correo"] for u in lista] == ["laura@cbtis.mx"]
    assert "password_temporal" not in lista[0]


def test_alta_de_usuario_valida_datos(client, headers_de):
    admin = headers_de("ADMINISTRADOR")
    base = {"nombre": "Laura", "correo": "laura@cbtis.mx", "roles": ["DOCENTE"]}
    assert client.post(f"{BASE}/usuarios", headers=admin, json={**base, "correo": "no-es-correo"}).status_code == 422
    assert client.post(f"{BASE}/usuarios", headers=admin, json={**base, "roles": ["INVENTADO"]}).status_code == 422
    assert client.post(f"{BASE}/usuarios", headers=admin, json={**base, "extra": 1}).status_code == 422
    assert client.post(f"{BASE}/usuarios", headers=admin, json=base).status_code == 201
    assert client.post(f"{BASE}/usuarios", headers=admin, json=base).status_code == 409


def test_actualizar_roles_y_desactivar_usuario(client, headers_de, login):
    admin = headers_de("ADMINISTRADOR")
    r = client.post(f"{BASE}/usuarios", headers=admin,
                    json={"nombre": "Luis", "correo": "luis@cbtis.mx", "roles": ["DOCENTE"]}).get_json()
    uid, temporal = r["usuario"]["id"], r["password_temporal"]

    r2 = client.patch(f"{BASE}/usuarios/{uid}", headers=admin, json={"roles": ["DOCENTE", "PREFECTO"]})
    assert r2.status_code == 200 and r2.get_json()["roles"] == ["DOCENTE", "PREFECTO"]

    client.patch(f"{BASE}/usuarios/{uid}", headers=admin, json={"activo": False})
    assert login("luis@cbtis.mx", temporal).status_code == 401

    nueva = client.post(f"{BASE}/usuarios/{uid}/restablecer-password", headers=admin).get_json()["password_temporal"]
    assert nueva != temporal


def test_el_administrador_no_puede_desactivarse_a_si_mismo(client, crear_usuario, login):
    correo, pwd = crear_usuario("root@cbtis.mx", ["ADMINISTRADOR"])
    h = {"Authorization": f"Bearer {login(correo, pwd).get_json()['access_token']}"}
    mi_id = client.get(f"{BASE}/auth/me", headers=h).get_json()["id"]
    assert client.patch(f"{BASE}/usuarios/{mi_id}", headers=h, json={"activo": False}).status_code == 422


def test_flujo_academico_completo(client, headers_de):
    admin = headers_de("ADMINISTRADOR")

    carrera = client.post(f"{BASE}/carreras", headers=admin, json={"nombre": "Programación", "clave": "prog"}).get_json()
    assert carrera["clave"] == "PROG"
    assert client.post(f"{BASE}/carreras", headers=admin, json={"nombre": "Otra", "clave": "PROG"}).status_code == 409

    g = client.post(f"{BASE}/grupos", headers=admin, json={"carrera_id": carrera["id"], "semestre": 1, "letra": "g"})
    assert g.status_code == 201 and g.get_json()["clave"] == "1G"
    assert client.post(f"{BASE}/grupos", headers=admin, json={"carrera_id": carrera["id"], "semestre": 7, "letra": "G"}).status_code == 422
    assert client.post(f"{BASE}/grupos", headers=admin, json={"carrera_id": carrera["id"], "semestre": 1, "letra": "G"}).status_code == 409

    p1 = client.post(f"{BASE}/periodos", headers=admin,
                     json={"nombre": "2026-A", "fecha_inicio": "2026-08-01", "fecha_fin": "2027-01-31"}).get_json()
    p2 = client.post(f"{BASE}/periodos", headers=admin,
                     json={"nombre": "2026-B", "fecha_inicio": "2027-02-01", "fecha_fin": "2027-07-01"}).get_json()
    client.post(f"{BASE}/periodos/{p1['id']}/vigente", headers=admin)
    client.post(f"{BASE}/periodos/{p2['id']}/vigente", headers=admin)
    vigentes = [p["nombre"] for p in client.get(f"{BASE}/periodos", headers=admin).get_json() if p["vigente"]]
    assert vigentes == ["2026-B"]
    assert client.post(f"{BASE}/periodos", headers=admin,
                       json={"nombre": "X", "fecha_inicio": "2027-02-01", "fecha_fin": "2027-01-01"}).status_code == 422

    docente = client.post(f"{BASE}/usuarios", headers=admin,
                          json={"nombre": "Profe", "correo": "profe@cbtis.mx", "roles": ["DOCENTE"]}).get_json()["usuario"]
    a = client.post(f"{BASE}/asignaciones-tutor", headers=admin,
                    json={"usuario_id": docente["id"], "grupo_id": g.get_json()["id"], "periodo_id": p1["id"]})
    assert a.status_code == 201 and a.get_json()["grupo_clave"] == "1G"
    assert client.post(f"{BASE}/asignaciones-tutor", headers=admin,
                       json={"usuario_id": docente["id"], "grupo_id": g.get_json()["id"], "periodo_id": p1["id"]}).status_code == 409
    assert client.delete(f"{BASE}/asignaciones-tutor/{a.get_json()['id']}", headers=admin).status_code == 200
    assert client.get(f"{BASE}/asignaciones-tutor", headers=admin).get_json() == []


def test_catalogos_legibles_por_cualquier_usuario_autenticado(client, headers_de):
    admin = headers_de("ADMINISTRADOR")
    prefecto = headers_de("PREFECTO")
    client.post(f"{BASE}/tipos-incidencia", headers=admin, json={"nombre": "Pelea"})
    client.post(f"{BASE}/tipos-sancion", headers=admin, json={"nombre": "Carta compromiso"})
    assert [t["nombre"] for t in client.get(f"{BASE}/tipos-incidencia", headers=prefecto).get_json()] == ["Pelea"]
    assert client.get(f"{BASE}/tipos-sancion", headers=prefecto).status_code == 200
    assert client.post(f"{BASE}/tipos-incidencia", headers=prefecto, json={"nombre": "X"}).status_code == 403
    assert client.get(f"{BASE}/carreras").status_code == 401
