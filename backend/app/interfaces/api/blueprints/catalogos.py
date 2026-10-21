from flask import Blueprint, jsonify

from app.domain.policies.politica_permisos import Permiso
from app.interfaces.api.helpers import arg_bool, contenedor, leer, parametros_cambiados
from app.interfaces.api.middlewares.auth import requiere_autenticacion, requiere_permiso
from app.interfaces.api.schemas.catalogos import (
    TipoIncidenciaActualizarIn, TipoIncidenciaCrearIn, TipoSancionActualizarIn, TipoSancionCrearIn,
)
from app.interfaces.api.serializadores import tipo_incidencia_a_dict, tipo_sancion_a_dict

bp = Blueprint("catalogos", __name__)
ADMIN = Permiso.ADMINISTRAR_CATALOGOS


@bp.get("/tipos-incidencia")
@requiere_autenticacion
def listar_tipos_incidencia():
    tipos = contenedor().listar_tipos_incidencia().ejecutar(solo_activos=bool(arg_bool("solo_activos")))
    return jsonify([tipo_incidencia_a_dict(t) for t in tipos])


@bp.post("/tipos-incidencia")
@requiere_permiso(ADMIN)
def crear_tipo_incidencia():
    d = leer(TipoIncidenciaCrearIn)
    return jsonify(tipo_incidencia_a_dict(contenedor().crear_tipo_incidencia().ejecutar(d.nombre))), 201


@bp.patch("/tipos-incidencia/<int:tipo_id>")
@requiere_permiso(ADMIN)
def actualizar_tipo_incidencia(tipo_id: int):
    cambios = parametros_cambiados(leer(TipoIncidenciaActualizarIn))
    tipo = contenedor().actualizar_tipo_incidencia().ejecutar(tipo_id, **cambios)
    return jsonify(tipo_incidencia_a_dict(tipo))


@bp.get("/tipos-sancion")
@requiere_autenticacion
def listar_tipos_sancion():
    tipos = contenedor().listar_tipos_sancion().ejecutar(solo_activos=bool(arg_bool("solo_activos")))
    return jsonify([tipo_sancion_a_dict(t) for t in tipos])


@bp.post("/tipos-sancion")
@requiere_permiso(ADMIN)
def crear_tipo_sancion():
    d = leer(TipoSancionCrearIn)
    tipo = contenedor().crear_tipo_sancion().ejecutar(d.nombre, d.requiere_dias)
    return jsonify(tipo_sancion_a_dict(tipo)), 201


@bp.patch("/tipos-sancion/<int:tipo_id>")
@requiere_permiso(ADMIN)
def actualizar_tipo_sancion(tipo_id: int):
    cambios = parametros_cambiados(leer(TipoSancionActualizarIn))
    return jsonify(tipo_sancion_a_dict(contenedor().actualizar_tipo_sancion().ejecutar(tipo_id, **cambios)))
