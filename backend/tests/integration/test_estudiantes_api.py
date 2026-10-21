import io

BASE = "/api/v1"
TUTOR = {"nombre": "Laura Gómez", "telefono": "449 765 4321", "parentesco": "Madre"}
ENC = "numero_control,primer_apellido,segundo_apellido,nombres,telefono,correo,calle,numero,colonia,ciudad,generacion,grupo,tutor_nombre,tutor_parentesco,tutor_telefono,tutor_correo\n"


def _estudiante(control="24301080150001", grupo_id=None, **extra):
    return {"numero_control": control, "primer_apellido": "Pérez", "nombres": "Ana", "generacion": "2024-2027",
            "grupo_id": grupo_id, "tutores": [TUTOR], **extra}


def _preparar(client, admin):
    """Carrera con grupos 1G, 1H y 2G; periodos 2026-A (vigente) y 2026-B; 3G para el avance."""
    carrera = client.post(f"{BASE}/carreras", headers=admin, json={"nombre": "Programación", "clave": "PROG"}).get_json()
    grupos = {}
    for clave in ("1G", "1H", "2G", "3G"):
        grupos[clave] = client.post(f"{BASE}/grupos", headers=admin,
                                    json={"carrera_id": carrera["id"], "semestre": int(clave[0]), "letra": clave[1]}).get_json()
    a = client.post(f"{BASE}/periodos", headers=admin,
                    json={"nombre": "2026-A", "fecha_inicio": "2026-08-01", "fecha_fin": "2027-01-31"}).get_json()
    b = client.post(f"{BASE}/periodos", headers=admin,
                    json={"nombre": "2026-B", "fecha_inicio": "2027-02-01", "fecha_fin": "2027-07-01"}).get_json()
    client.post(f"{BASE}/periodos/{a['id']}/vigente", headers=admin)
    return {"grupos": grupos, "a": a, "b": b}


def test_crear_y_consultar_estudiante_con_permisos(client, headers_de):
    admin, orient, docente = headers_de("ADMINISTRADOR"), headers_de("ORIENTACION"), headers_de("DOCENTE")
    ctx = _preparar(client, admin)
    cuerpo = _estudiante(grupo_id=ctx["grupos"]["1G"]["id"])

    assert client.post(f"{BASE}/estudiantes", headers=docente, json=cuerpo).status_code == 403
    r = client.post(f"{BASE}/estudiantes", headers=orient, json=cuerpo)
    assert r.status_code == 201
    d = r.get_json()
    assert d["grupo_actual"] == "1G" and d["tutores_legales"][0]["telefono"] == "4497654321"
    assert d["tutores_legales"][0]["es_principal"] is True
    assert client.post(f"{BASE}/estudiantes", headers=orient, json=cuerpo).status_code == 409
    assert client.post(f"{BASE}/estudiantes", headers=orient, json={**cuerpo, "numero_control": "1"}).status_code == 422

    assert client.get(f"{BASE}/estudiantes/{d['id']}", headers=orient).status_code == 200
    assert client.get(f"{BASE}/estudiantes/{d['id']}", headers=docente).status_code == 403
    assert client.get(f"{BASE}/estudiantes", headers=docente).status_code == 403


def test_buscador_no_expone_datos_de_contacto(client, headers_de):
    admin, prefecto = headers_de("ADMINISTRADOR"), headers_de("PREFECTO")
    ctx = _preparar(client, admin)
    client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante(grupo_id=ctx["grupos"]["1G"]["id"],
                                                                         telefono="4491234567", calle="Av. X"))
    r = client.get(f"{BASE}/estudiantes/buscar?q=pérez", headers=prefecto)
    assert r.status_code == 200
    item = r.get_json()[0]
    assert set(item) == {"id", "numero_control", "nombre_completo", "grupo", "carrera"}
    assert client.get(f"{BASE}/estudiantes/buscar?q=p", headers=prefecto).status_code == 422


def test_tutor_ve_solo_estudiantes_de_su_grupo(client, headers_de):
    admin, tutor = headers_de("ADMINISTRADOR"), headers_de("DOCENTE")
    ctx = _preparar(client, admin)
    mio = client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante("24301080150001", ctx["grupos"]["1G"]["id"])).get_json()
    otro = client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante("24301080150002", ctx["grupos"]["1H"]["id"])).get_json()

    tutor_id = client.get(f"{BASE}/auth/me", headers=tutor).get_json()["id"]
    assert client.get(f"{BASE}/auth/me", headers=tutor).get_json()["grupos_tutelados"] == []
    client.post(f"{BASE}/asignaciones-tutor", headers=admin,
                json={"usuario_id": tutor_id, "grupo_id": ctx["grupos"]["1G"]["id"], "periodo_id": ctx["a"]["id"]})

    assert client.get(f"{BASE}/auth/me", headers=tutor).get_json()["grupos_tutelados"] == ["1G"]
    lista = client.get(f"{BASE}/estudiantes", headers=tutor).get_json()
    assert [e["id"] for e in lista] == [mio["id"]]
    assert client.get(f"{BASE}/estudiantes/{mio['id']}", headers=tutor).status_code == 200
    assert client.get(f"{BASE}/estudiantes/{otro['id']}", headers=tutor).status_code == 403


def test_editar_estudiante_y_tutores_legales(client, headers_de):
    admin = headers_de("ADMINISTRADOR")
    ctx = _preparar(client, admin)
    d = client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante(grupo_id=ctx["grupos"]["1G"]["id"])).get_json()

    r = client.patch(f"{BASE}/estudiantes/{d['id']}", headers=admin, json={"nombres": "Ana Sofía", "estatus": "BAJA"})
    assert r.status_code == 200 and r.get_json()["estatus"] == "BAJA"
    assert client.patch(f"{BASE}/estudiantes/{d['id']}", headers=admin, json={"numero_control": "X1234"}).status_code == 422

    t = client.post(f"{BASE}/estudiantes/{d['id']}/tutores-legales", headers=admin,
                    json={"nombre": "Pedro Pérez", "telefono": "4491112233", "es_principal": True})
    assert t.status_code == 201 and [x["nombre"] for x in t.get_json() if x["es_principal"]] == ["Pedro Pérez"]
    unico = [x for x in t.get_json() if x["nombre"] == "Laura Gómez"][0]
    assert client.delete(f"{BASE}/tutores-legales/{unico['id']}", headers=admin).status_code == 200
    ultimo = client.get(f"{BASE}/estudiantes/{d['id']}", headers=admin).get_json()["tutores_legales"][0]
    assert client.delete(f"{BASE}/tutores-legales/{ultimo['id']}", headers=admin).status_code == 422


def test_importar_csv_reporta_omitidos_y_errores(client, headers_de):
    admin, orient = headers_de("ADMINISTRADOR"), headers_de("ORIENTACION")
    ctx = _preparar(client, admin)
    client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante("24301080150001", ctx["grupos"]["1G"]["id"]))

    fila = lambda c, g="1G": f"{c},Pérez,,Ana,,,,,,,2024-2027,{g},Laura,Madre,4497654321,\n"  # noqa: E731
    csv = (ENC + fila("24301080150001") + fila("24301080150002") + fila("24301080150003", "9Z")).encode("utf-8")
    envio = lambda h: client.post(f"{BASE}/estudiantes/importar", headers=h, content_type="multipart/form-data",  # noqa: E731
                                  data={"archivo": (io.BytesIO(csv), "alumnos.csv")})
    assert envio(orient).status_code == 403  # solo el Administrador importa
    r = envio(admin)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["creados"] == 1 and len(datos["omitidos"]) == 1 and len(datos["errores"]) == 1
    sin_archivo = client.post(f"{BASE}/estudiantes/importar", headers=admin, content_type="multipart/form-data", data={})
    assert sin_archivo.status_code == 422


def test_descargar_plantilla(client, headers_de):
    admin = headers_de("ADMINISTRADOR")
    r = client.get(f"{BASE}/estudiantes/plantilla", headers=admin)
    assert r.status_code == 200 and r.mimetype == "text/csv"
    assert r.get_data(as_text=True).splitlines()[0].lstrip("\ufeff").startswith("numero_control,")


def test_avance_de_semestre_simula_y_luego_ejecuta(client, headers_de):
    admin, orient = headers_de("ADMINISTRADOR"), headers_de("ORIENTACION")
    ctx = _preparar(client, admin)
    ids = [client.post(f"{BASE}/estudiantes", headers=admin, json=_estudiante(f"2430108015000{n}", ctx["grupos"]["1G"]["id"])).get_json()["id"]
           for n in (1, 2, 3)]
    cuerpo = {"periodo_origen_id": ctx["a"]["id"], "periodo_destino_id": ctx["b"]["id"],
              "excepciones": [{"estudiante_id": ids[1], "accion": "REPETIR"}, {"estudiante_id": ids[2], "accion": "BAJA"}]}

    assert client.post(f"{BASE}/estudiantes/avance-semestre", headers=orient, json=cuerpo).status_code == 403
    sim = client.post(f"{BASE}/estudiantes/avance-semestre", headers=admin, json=cuerpo).get_json()  # simular por defecto
    assert sim["ejecutado"] is False and sim["conteo"] == {"AVANZA": 1, "REPITE": 1, "BAJA": 1}

    ok = client.post(f"{BASE}/estudiantes/avance-semestre", headers=admin, json={**cuerpo, "simular": False})
    assert ok.status_code == 200 and ok.get_json()["ejecutado"] is True
    client.post(f"{BASE}/periodos/{ctx['b']['id']}/vigente", headers=admin)
    ficha = client.get(f"{BASE}/estudiantes/{ids[0]}", headers=admin).get_json()
    assert ficha["grupo_actual"] == "2G" and [h["grupo"] for h in ficha["historial"]] == ["1G", "2G"]
    assert client.get(f"{BASE}/estudiantes/{ids[2]}", headers=admin).get_json()["estatus"] == "BAJA"
