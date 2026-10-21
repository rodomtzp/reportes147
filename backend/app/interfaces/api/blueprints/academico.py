from flask import Blueprint, jsonify, request

from app.domain.policies.politica_permisos import Permiso
from app.interfaces.api.helpers import arg_bool, contenedor, leer, parametros_cambiados
from app.interfaces.api.middlewares.auth import requiere_autenticacion, requiere_permiso
from app.interfaces.api.schemas.academico import (
    AsignacionTutorCrearIn, CarreraActualizarIn, CarreraCrearIn, GrupoActualizarIn,
    GrupoCrearIn, PeriodoActualizarIn, PeriodoCrearIn,
)
from app.interfaces.api.serializadores import (
    asignacion_a_dict, carrera_a_dict, grupo_a_dict, periodo_a_dict,
)

bp = Blueprint("academico", __name__)
ADMIN = Permiso.ADMINISTRAR_CATALOGOS


# ---- Carreras (lectura: cualquier usuario autenticado; escritura: administrador) ----
@bp.get("/carreras")
@requiere_autenticacion
def listar_carreras():
    carreras = contenedor().listar_carreras().ejecutar(solo_activas=bool(arg_bool("solo_activas")))
    return jsonify([carrera_a_dict(c) for c in carreras])


@bp.post("/carreras")
@requiere_permiso(ADMIN)
def crear_carrera():
    d = leer(CarreraCrearIn)
    return jsonify(carrera_a_dict(contenedor().crear_carrera().ejecutar(d.nombre, d.clave))), 201


@bp.patch("/carreras/<int:carrera_id>")
@requiere_permiso(ADMIN)
def actualizar_carrera(carrera_id: int):
    cambios = parametros_cambiados(leer(CarreraActualizarIn))
    return jsonify(carrera_a_dict(contenedor().actualizar_carrera().ejecutar(carrera_id, **cambios)))


# ---- Grupos ----
@bp.get("/grupos")
@requiere_autenticacion
def listar_grupos():
    grupos = contenedor().listar_grupos().ejecutar(
        carrera_id=request.args.get("carrera_id", type=int),
        semestre=request.args.get("semestre", type=int),
        solo_activos=bool(arg_bool("solo_activos")),
    )
    return jsonify([grupo_a_dict(g) for g in grupos])


@bp.post("/grupos")
@requiere_permiso(ADMIN)
def crear_grupo():
    d = leer(GrupoCrearIn)
    return jsonify(grupo_a_dict(contenedor().crear_grupo().ejecutar(d.carrera_id, d.semestre, d.letra))), 201


@bp.patch("/grupos/<int:grupo_id>")
@requiere_permiso(ADMIN)
def actualizar_grupo(grupo_id: int):
    cambios = parametros_cambiados(leer(GrupoActualizarIn))
    return jsonify(grupo_a_dict(contenedor().actualizar_grupo().ejecutar(grupo_id, **cambios)))


# ---- Periodos escolares ----
@bp.get("/periodos")
@requiere_autenticacion
def listar_periodos():
    return jsonify([periodo_a_dict(p) for p in contenedor().listar_periodos().ejecutar()])


@bp.post("/periodos")
@requiere_permiso(ADMIN)
def crear_periodo():
    d = leer(PeriodoCrearIn)
    periodo = contenedor().crear_periodo().ejecutar(d.nombre, d.fecha_inicio, d.fecha_fin)
    return jsonify(periodo_a_dict(periodo)), 201


@bp.patch("/periodos/<int:periodo_id>")
@requiere_permiso(ADMIN)
def actualizar_periodo(periodo_id: int):
    cambios = parametros_cambiados(leer(PeriodoActualizarIn))
    return jsonify(periodo_a_dict(contenedor().actualizar_periodo().ejecutar(periodo_id, **cambios)))


@bp.post("/periodos/<int:periodo_id>/vigente")
@requiere_permiso(ADMIN)
def establecer_periodo_vigente(periodo_id: int):
    return jsonify(periodo_a_dict(contenedor().establecer_periodo_vigente().ejecutar(periodo_id)))


# ---- Asignación de tutores ----
@bp.get("/asignaciones-tutor")
@requiere_permiso(ADMIN)
def listar_asignaciones_tutor():
    detalles = contenedor().listar_asignaciones_tutor().ejecutar(
        periodo_id=request.args.get("periodo_id", type=int),
        grupo_id=request.args.get("grupo_id", type=int),
        usuario_id=request.args.get("usuario_id", type=int),
    )
    return jsonify([asignacion_a_dict(d) for d in detalles])


@bp.post("/asignaciones-tutor")
@requiere_permiso(ADMIN)
def asignar_tutor():
    d = leer(AsignacionTutorCrearIn)
    detalle = contenedor().asignar_tutor().ejecutar(d.usuario_id, d.grupo_id, d.periodo_id)
    return jsonify(asignacion_a_dict(detalle)), 201


@bp.delete("/asignaciones-tutor/<int:asignacion_id>")
@requiere_permiso(ADMIN)
def retirar_asignacion_tutor(asignacion_id: int):
    contenedor().retirar_asignacion_tutor().ejecutar(asignacion_id)
    return jsonify(mensaje="Asignación retirada.")
