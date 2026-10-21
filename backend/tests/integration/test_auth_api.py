def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.get_json() == {"estado": "ok"}


def test_login_y_me_devuelven_roles_y_permisos(client, crear_usuario, login):
    correo, pwd = crear_usuario("orient@cbtis.mx", ["ORIENTACION"])
    r = login(correo, pwd)
    assert r.status_code == 200
    me = client.get("/api/v1/auth/me", headers=_auth(r.get_json()["access_token"]))
    assert me.status_code == 200
    datos = me.get_json()
    assert datos["roles"] == ["ORIENTACION"]
    assert "REGISTRAR_LLAMADAS" in datos["permisos"]
    assert "APLICAR_SANCIONES" not in datos["permisos"]
    assert "password_hash" not in datos


def test_login_invalido_devuelve_401_generico(client, crear_usuario, login):
    crear_usuario("a@cbtis.mx", ["DOCENTE"])
    r1 = login("a@cbtis.mx", "incorrecta-123456")
    r2 = login("no-existe@cbtis.mx", "incorrecta-123456")
    assert r1.status_code == r2.status_code == 401
    assert r1.get_json() == r2.get_json()


def test_me_sin_token_o_con_refresh_devuelve_401(client, crear_usuario, login):
    correo, pwd = crear_usuario("b@cbtis.mx", ["DOCENTE"])
    assert client.get("/api/v1/auth/me").status_code == 401
    refresh = login(correo, pwd).get_json()["refresh_token"]
    assert client.get("/api/v1/auth/me", headers=_auth(refresh)).status_code == 401


def test_refresh_entrega_nuevo_access(client, crear_usuario, login):
    correo, pwd = crear_usuario("c@cbtis.mx", ["PREFECTO"])
    refresh = login(correo, pwd).get_json()["refresh_token"]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    me = client.get("/api/v1/auth/me", headers=_auth(r.get_json()["access_token"]))
    assert me.get_json()["roles"] == ["PREFECTO"]


def test_requiere_permiso_devuelve_403(app, client, crear_usuario, login):
    """Ruta de prueba protegida por permiso: el decorador debe negar al prefecto."""
    from app.domain.policies.politica_permisos import Permiso
    from app.interfaces.api.middlewares.auth import requiere_permiso

    @app.get("/api/v1/_solo_sanciones")
    @requiere_permiso(Permiso.APLICAR_SANCIONES)
    def _ruta():
        return {"ok": True}

    pref, p1 = crear_usuario("pref@cbtis.mx", ["PREFECTO"])
    sub, p2 = crear_usuario("sub@cbtis.mx", ["SUBDIRECCION"])
    t_pref = login(pref, p1).get_json()["access_token"]
    t_sub = login(sub, p2).get_json()["access_token"]
    assert client.get("/api/v1/_solo_sanciones", headers=_auth(t_pref)).status_code == 403
    assert client.get("/api/v1/_solo_sanciones", headers=_auth(t_sub)).status_code == 200


def test_usuario_desactivado_pierde_acceso_de_inmediato(app, client, crear_usuario, login):
    from app.infrastructure.persistence.models import UsuarioModel

    correo, pwd = crear_usuario("d@cbtis.mx", ["DOCENTE"])
    token = login(correo, pwd).get_json()["access_token"]
    s = app.extensions["container"].session_factory()
    s.query(UsuarioModel).filter_by(correo=correo).one().activo = False
    s.commit()
    s.close()
    assert client.get("/api/v1/auth/me", headers=_auth(token)).status_code == 401


def test_password_temporal_bloquea_la_api_hasta_cambiarla(client, crear_usuario, login):
    correo, temporal = crear_usuario("nuevo@cbtis.mx", ["ADMINISTRADOR"], password="temporal-12345", debe_cambiar=True)
    h = _auth(login(correo, temporal).get_json()["access_token"])

    me = client.get("/api/v1/auth/me", headers=h)  # permitido para poder mostrar la pantalla de cambio
    assert me.status_code == 200 and me.get_json()["debe_cambiar_password"] is True

    bloqueado = client.get("/api/v1/carreras", headers=h)
    assert bloqueado.status_code == 403 and bloqueado.get_json()["codigo"] == "CAMBIO_PASSWORD_REQUERIDO"

    r = client.post("/api/v1/auth/cambiar-password", headers=h,
                    json={"password_actual": temporal, "password_nueva": "mi-clave-definitiva-1"})
    assert r.status_code == 200

    h2 = _auth(login(correo, "mi-clave-definitiva-1").get_json()["access_token"])
    assert client.get("/api/v1/carreras", headers=h2).status_code == 200
    assert login(correo, temporal).status_code == 401  # la temporal ya no sirve


def test_cambiar_password_con_actual_incorrecta_devuelve_422(client, crear_usuario, login):
    correo, pwd = crear_usuario("e@cbtis.mx", ["DOCENTE"])
    h = _auth(login(correo, pwd).get_json()["access_token"])
    r = client.post("/api/v1/auth/cambiar-password", headers=h,
                    json={"password_actual": "incorrecta-1234", "password_nueva": "otra-clave-larga-1"})
    assert r.status_code == 422


def test_login_sin_campos_devuelve_422(client):
    assert client.post("/api/v1/auth/login", json={}).status_code == 422


def test_cinco_intentos_fallidos_bloquean_con_429(client, crear_usuario, login):
    correo, pwd = crear_usuario("bloq@cbtis.mx", ["DOCENTE"])
    for _ in range(4):
        assert login(correo, "incorrecta-1234").status_code == 401
    quinto = login(correo, "incorrecta-1234")
    assert quinto.status_code == 429 and quinto.get_json()["codigo"] == "CUENTA_BLOQUEADA"
    assert login(correo, pwd).status_code == 429                    # ni con la clave correcta
    otro, otro_pwd = crear_usuario("libre@cbtis.mx", ["DOCENTE"])
    assert login(otro, otro_pwd).status_code == 200                # el bloqueo es por cuenta


def test_cambiar_password_cierra_la_sesion_anterior_y_entrega_tokens_nuevos(client, crear_usuario, login):
    correo, pwd = crear_usuario("cambio@cbtis.mx", ["DOCENTE"])
    viejo = login(correo, pwd).get_json()
    h_viejo = _auth(viejo["access_token"])
    r = client.post("/api/v1/auth/cambiar-password", headers=h_viejo,
                    json={"password_actual": pwd, "password_nueva": "mi-clave-definitiva-1"})
    assert r.status_code == 200
    nuevo = r.get_json()
    assert client.get("/api/v1/auth/me", headers=h_viejo).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": viejo["refresh_token"]}).status_code == 401
    assert client.get("/api/v1/auth/me", headers=_auth(nuevo["access_token"])).status_code == 200


def test_restablecer_password_cierra_sesiones_y_desbloquea(client, crear_usuario, login, headers_de):
    admin = headers_de("ADMINISTRADOR")
    correo, pwd = crear_usuario("reset@cbtis.mx", ["DOCENTE"])
    sesion = _auth(login(correo, pwd).get_json()["access_token"])
    uid = client.get("/api/v1/auth/me", headers=sesion).get_json()["id"]
    for _ in range(5):
        login(correo, "incorrecta-1234")
    assert login(correo, pwd).status_code == 429
    temporal = client.post(f"/api/v1/usuarios/{uid}/restablecer-password", headers=admin).get_json()
    assert client.get("/api/v1/auth/me", headers=sesion).status_code == 401
    clave = temporal["password_temporal"]
    assert login(correo, clave).status_code == 200


def test_cabeceras_de_seguridad(client):
    r = client.get("/api/v1/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["Cache-Control"] == "no-store" and r.headers["Referrer-Policy"] == "no-referrer"
