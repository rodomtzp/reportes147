from flask import Blueprint, g, jsonify

from app.domain.policies.politica_permisos import permisos_de
from app.interfaces.api.helpers import contenedor, leer
from app.interfaces.api.middlewares.auth import requiere_autenticacion
from app.interfaces.api.schemas.auth import CambiarPasswordIn, LoginIn, RefreshIn

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    datos = leer(LoginIn)
    tokens = contenedor().iniciar_sesion().ejecutar(datos.correo, datos.password)
    return jsonify(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@bp.post("/refresh")
def refresh():
    datos = leer(RefreshIn)
    return jsonify(access_token=contenedor().renovar_token().ejecutar(datos.refresh_token))


@bp.get("/me")
@requiere_autenticacion(permitir_password_pendiente=True)
def me():
    u = g.usuario
    return jsonify(
        id=u.id,
        nombre=u.nombre,
        correo=u.correo,
        roles=sorted(r.value for r in u.roles),
        permisos=sorted(p.value for p in permisos_de(u.roles)),
        debe_cambiar_password=u.debe_cambiar_password,
        grupos_tutelados=[] if u.debe_cambiar_password else contenedor().grupos_tutelados().ejecutar(u),
    )


@bp.post("/cambiar-password")
@requiere_autenticacion(permitir_password_pendiente=True)
def cambiar_password():
    datos = leer(CambiarPasswordIn)
    tokens = contenedor().cambiar_password().ejecutar(g.usuario.id, datos.password_actual, datos.password_nueva)
    # Las demás sesiones quedan cerradas; esta recibe tokens nuevos.
    return jsonify(mensaje="Contraseña actualizada.", access_token=tokens.access_token, refresh_token=tokens.refresh_token)
