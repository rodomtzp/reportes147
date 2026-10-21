from urllib.parse import quote

from flask import Blueprint, Response, g, jsonify, request

from app.application.dto.exportaciones import TIPO_XLSX
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_permisos import Permiso
from app.domain.value_objects.accion_bitacora import AccionBitacora
from app.interfaces.api.helpers import arg_bool, arg_enum, arg_fecha, contenedor
from app.interfaces.api.middlewares.auth import requiere_autenticacion, requiere_permiso
from app.interfaces.api.serializadores import bitacora_a_dict

bp = Blueprint("exportaciones", __name__)


def _excel(alcance: str, objetivo_id: int) -> Response:
    archivo = contenedor().exportar_reportes().ejecutar(
        g.usuario, alcance, objetivo_id, incluir_contacto=bool(arg_bool("incluir_contacto")),
        desde=arg_fecha("desde"), hasta=arg_fecha("hasta", fin_de_dia=True))
    return Response(archivo.contenido, mimetype=TIPO_XLSX, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(archivo.nombre)}",
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
    })


@bp.get("/exportaciones/estudiantes/<int:estudiante_id>")
@requiere_autenticacion
def exportar_por_estudiante(estudiante_id: int):
    return _excel("estudiante", estudiante_id)


@bp.get("/exportaciones/grupos/<int:grupo_id>")
@requiere_autenticacion
def exportar_por_grupo(grupo_id: int):
    return _excel("grupo", grupo_id)


@bp.get("/exportaciones/carreras/<int:carrera_id>")
@requiere_autenticacion
def exportar_por_carrera(carrera_id: int):
    return _excel("carrera", carrera_id)


@bp.get("/bitacora")
@requiere_permiso(Permiso.CONSULTAR_BITACORA)
def consultar_bitacora():
    a = request.args
    registros = contenedor().consultar_bitacora().ejecutar(
        accion=arg_enum("accion", AccionBitacora), usuario_id=a.get("usuario_id", type=int),
        estudiante_id=a.get("estudiante_id", type=int), desde=arg_fecha("desde"),
        hasta=arg_fecha("hasta", fin_de_dia=True),
        limite=a.get("limite", default=100, type=int), offset=a.get("offset", default=0, type=int))
    return jsonify([bitacora_a_dict(r) for r in registros])
