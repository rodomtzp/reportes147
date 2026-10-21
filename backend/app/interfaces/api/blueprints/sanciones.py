from flask import Blueprint, g, jsonify, request

from app.domain.policies.politica_permisos import Permiso
from app.interfaces.api.helpers import arg_bool, contenedor, leer
from app.interfaces.api.middlewares.auth import requiere_permiso
from app.interfaces.api.schemas.sanciones import SancionIn
from app.interfaces.api.serializadores import expediente_a_dict, notificacion_a_dict, reporte_detalle_a_dict

bp = Blueprint("sanciones", __name__)


@bp.post("/reportes/<int:reporte_id>/sancion")
@requiere_permiso(Permiso.APLICAR_SANCIONES)
def aplicar_sancion_directa(reporte_id: int):
    """Sanción por la magnitud de un reporte Grave o Muy grave."""
    d = leer(SancionIn)
    contenedor().aplicar_sancion_directa().ejecutar(g.usuario.id, reporte_id, d.tipo_sancion_id, d.dias, d.observaciones)
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id))), 201


@bp.post("/estudiantes/<int:estudiante_id>/sancion-acumulacion")
@requiere_permiso(Permiso.APLICAR_SANCIONES)
def aplicar_sancion_por_acumulacion(estudiante_id: int):
    """Con 3 o más reportes en el ciclo: una sanción que cubre todos y reinicia el contador."""
    d = leer(SancionIn)
    contenedor().aplicar_sancion_por_acumulacion().ejecutar(g.usuario.id, estudiante_id, d.tipo_sancion_id, d.dias, d.observaciones)
    return jsonify(expediente_a_dict(contenedor().obtener_expediente().ejecutar(estudiante_id))), 201


@bp.get("/estudiantes/<int:estudiante_id>/expediente")
@requiere_permiso(Permiso.VER_TODOS_LOS_REPORTES)
def expediente_disciplinario(estudiante_id: int):
    return jsonify(expediente_a_dict(contenedor().obtener_expediente().ejecutar(estudiante_id)))


# ---- Bandeja de alertas (Subdirección y Dirección) ----
@bp.get("/alertas")
@requiere_permiso(Permiso.VER_ALERTAS)
def listar_alertas():
    pagina = contenedor().listar_alertas().ejecutar(
        solo_pendientes=arg_bool("pendientes") is not False,   # por defecto, solo las pendientes
        limite=request.args.get("limite", default=100, type=int), offset=request.args.get("offset", default=0, type=int))
    return jsonify({"pendientes": pagina.pendientes, "alertas": [notificacion_a_dict(n) for n in pagina.notificaciones]})


@bp.get("/alertas/resumen")
@requiere_permiso(Permiso.VER_ALERTAS)
def resumen_alertas():
    return jsonify({"pendientes": contenedor().contar_alertas_pendientes().ejecutar()})


@bp.post("/alertas/<int:alerta_id>/atendida")
@requiere_permiso(Permiso.VER_ALERTAS)
def marcar_alerta_atendida(alerta_id: int):
    return jsonify(notificacion_a_dict(contenedor().marcar_alerta_atendida().ejecutar(g.usuario.id, alerta_id)))
