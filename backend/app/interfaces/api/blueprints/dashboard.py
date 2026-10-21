from flask import Blueprint, g, jsonify, request

from app.interfaces.api.helpers import contenedor
from app.interfaces.api.middlewares.auth import requiere_autenticacion

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@requiere_autenticacion
def dashboard():
    d = contenedor().obtener_dashboard().ejecutar(g.usuario, request.args.get("rango", "periodo"))
    par = lambda lista: [{"etiqueta": e, "valor": v} for e, v in lista]  # noqa: E731
    return jsonify(
        rango=d.rango, desde=d.desde.isoformat(), hasta=d.hasta.isoformat(), granularidad=d.granularidad,
        periodo=d.periodo_nombre, alcance=d.alcance,
        total_rango=d.total_rango, mes_actual=d.mes_actual, mes_anterior=d.mes_anterior,
        por_gravedad=par(d.por_gravedad), pendientes_llamada=d.pendientes_llamada,
        alertas_pendientes=d.alertas_pendientes,
        en_riesgo=[{"estudiante_id": e.estudiante_id, "estudiante": e.estudiante, "grupo": e.grupo, "total": e.total}
                   for e in d.en_riesgo],
        total_en_riesgo=d.total_en_riesgo, listos_para_sancion=d.listos_para_sancion,
        serie=par(d.serie), por_grupo=par(d.por_grupo), por_carrera=par(d.por_carrera),
        por_tipo=par(d.por_tipo), por_estado=par(d.por_estado),
    )
