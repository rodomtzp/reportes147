from flask import Blueprint, g, jsonify

from app.domain.policies.politica_permisos import Permiso
from app.domain.value_objects.rol import Rol
from app.interfaces.api.helpers import arg_bool, arg_enum, contenedor, leer, parametros_cambiados
from app.interfaces.api.middlewares.auth import requiere_permiso
from app.interfaces.api.schemas.usuarios import UsuarioActualizarIn, UsuarioCrearIn
from app.interfaces.api.serializadores import usuario_a_dict

bp = Blueprint("usuarios", __name__)
GESTIONAR = Permiso.GESTIONAR_USUARIOS


@bp.get("/usuarios")
@requiere_permiso(GESTIONAR)
def listar_usuarios():
    usuarios = contenedor().listar_usuarios().ejecutar(
        rol=arg_enum("rol", Rol), activo=arg_bool("activo")
    )
    return jsonify([usuario_a_dict(u) for u in usuarios])


@bp.post("/usuarios")
@requiere_permiso(GESTIONAR)
def crear_usuario():
    datos = leer(UsuarioCrearIn)
    usuario, temporal = contenedor().registrar_usuario().ejecutar(datos.nombre, datos.correo, datos.roles)
    # La contraseña temporal solo se devuelve en esta respuesta.
    return jsonify(usuario=usuario_a_dict(usuario), password_temporal=temporal), 201


@bp.patch("/usuarios/<int:usuario_id>")
@requiere_permiso(GESTIONAR)
def actualizar_usuario(usuario_id: int):
    cambios = parametros_cambiados(leer(UsuarioActualizarIn))
    usuario = contenedor().actualizar_usuario().ejecutar(g.usuario.id, usuario_id, **cambios)
    return jsonify(usuario_a_dict(usuario))


@bp.post("/usuarios/<int:usuario_id>/restablecer-password")
@requiere_permiso(GESTIONAR)
def restablecer_password(usuario_id: int):
    temporal = contenedor().restablecer_password().ejecutar(usuario_id)
    return jsonify(password_temporal=temporal)
