from urllib.parse import quote

from flask import Blueprint, Response, g, jsonify, request

from app.application.dto.reportes import MAX_BYTES_ADJUNTO
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_permisos import Permiso
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.gravedad import Gravedad
from app.interfaces.api.helpers import arg_bool, arg_enum, arg_fecha, contenedor, leer, parametros_cambiados
from app.interfaces.api.middlewares.auth import requiere_autenticacion, requiere_permiso
from app.interfaces.api.schemas.reportes import (
    CambiarGravedadIn, CancelarIn, LlamadaIn, MensajeWhatsAppIn, ReporteCorregirIn, ReporteCrearIn, TurnarIn,
)
from app.interfaces.api.serializadores import (
    adjunto_a_dict, mensaje_generado_a_dict, mensaje_whatsapp_a_dict, reporte_creado_a_dict,
    reporte_detalle_a_dict, reporte_listado_a_dict, seguimiento_a_dict,
)

bp = Blueprint("reportes", __name__)


@bp.post("/reportes")
@requiere_permiso(Permiso.CREAR_REPORTE)
def crear_reportes():
    d = leer(ReporteCrearIn)
    creados = contenedor().crear_reportes().ejecutar(
        g.usuario, d.estudiante_ids, d.tipo_incidencia_id, d.descripcion, d.gravedad,
        descripcion_otro=d.descripcion_otro, fecha_hora_incidente=d.fecha_hora_incidente,
    )
    return jsonify([reporte_creado_a_dict(c) for c in creados]), 201


@bp.get("/reportes")
@requiere_autenticacion
def listar_reportes():
    a = request.args
    reportes = contenedor().listar_reportes().ejecutar(
        g.usuario,
        estudiante_id=a.get("estudiante_id", type=int), grupo_id=a.get("grupo_id", type=int),
        carrera_id=a.get("carrera_id", type=int), estado=arg_enum("estado", EstadoReporte),
        gravedad=arg_enum("gravedad", Gravedad), tipo_incidencia_id=a.get("tipo_incidencia_id", type=int),
        desde=arg_fecha("desde"), hasta=arg_fecha("hasta", fin_de_dia=True), texto=a.get("q"),
        incluir_cancelados=bool(arg_bool("incluir_cancelados")),
        sin_llamada_efectiva=bool(arg_bool("sin_llamada_efectiva")),
        limite=a.get("limite", default=100, type=int), offset=a.get("offset", default=0, type=int),
    )
    return jsonify([reporte_listado_a_dict(r) for r in reportes])


@bp.get("/reportes/<int:reporte_id>")
@requiere_autenticacion
def obtener_reporte(reporte_id: int):
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id)))


@bp.patch("/reportes/<int:reporte_id>")
@requiere_permiso(Permiso.CORREGIR_REPORTE)
def corregir_reporte(reporte_id: int):
    cambios = parametros_cambiados(leer(ReporteCorregirIn))
    contenedor().corregir_reporte().ejecutar(g.usuario.id, reporte_id, **cambios)
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id)))


@bp.post("/reportes/<int:reporte_id>/gravedad")
@requiere_permiso(Permiso.CAMBIAR_GRAVEDAD)
def cambiar_gravedad(reporte_id: int):
    d = leer(CambiarGravedadIn)
    contenedor().cambiar_gravedad().ejecutar(g.usuario.id, reporte_id, d.gravedad, d.motivo)
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id)))


@bp.post("/reportes/<int:reporte_id>/turnar")
@requiere_permiso(Permiso.TURNAR_A_SUBDIRECCION)
def turnar_a_subdireccion(reporte_id: int):
    d = leer(TurnarIn)
    contenedor().turnar_a_subdireccion().ejecutar(g.usuario.id, reporte_id, d.comentario)
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id)))


@bp.post("/reportes/<int:reporte_id>/cancelar")
@requiere_permiso(Permiso.CANCELAR_REPORTE)
def cancelar_reporte(reporte_id: int):
    d = leer(CancelarIn)
    contenedor().cancelar_reporte().ejecutar(g.usuario.id, reporte_id, d.motivo)
    return jsonify(reporte_detalle_a_dict(contenedor().obtener_reporte().ejecutar(g.usuario, reporte_id)))


@bp.post("/reportes/<int:reporte_id>/adjuntos")
@requiere_autenticacion
def agregar_adjunto(reporte_id: int):
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        raise ReglaDeNegocioViolada("Adjunta una imagen o PDF en el campo 'archivo'.")
    adjuntos = contenedor().agregar_adjunto().ejecutar(
        g.usuario, reporte_id, archivo.filename, archivo.read(MAX_BYTES_ADJUNTO + 1),
        aplicar_a_incidente=request.form.get("aplicar_a_incidente", "").lower() in ("1", "true", "si", "sí"),
    )
    return jsonify([adjunto_a_dict(a) for a in adjuntos]), 201


@bp.get("/reportes/<int:reporte_id>/adjuntos/<int:adjunto_id>")
@requiere_autenticacion
def descargar_adjunto(reporte_id: int, adjunto_id: int):
    adjunto, contenido = contenedor().obtener_adjunto().ejecutar(g.usuario, reporte_id, adjunto_id)
    return Response(
        contenido, mimetype=adjunto.tipo_mime,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(adjunto.nombre_original)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


# ---- Llamadas y mensajes de WhatsApp (Orientación Educativa) ----
@bp.get("/reportes/<int:reporte_id>/llamadas")
@requiere_permiso(Permiso.REGISTRAR_LLAMADAS)
def seguimiento_llamadas(reporte_id: int):
    return jsonify(seguimiento_a_dict(contenedor().obtener_seguimiento_llamadas().ejecutar(g.usuario.id, reporte_id)))


@bp.post("/reportes/<int:reporte_id>/llamadas")
@requiere_permiso(Permiso.REGISTRAR_LLAMADAS)
def registrar_llamada(reporte_id: int):
    d = leer(LlamadaIn)
    contenedor().registrar_llamada().ejecutar(
        g.usuario.id, reporte_id, d.estado, tutor_legal_id=d.tutor_legal_id,
        atendio_nombre=d.atendio_nombre, observaciones=d.observaciones, fecha_hora=d.fecha_hora,
    )
    return jsonify(seguimiento_a_dict(contenedor().obtener_seguimiento_llamadas().ejecutar(g.usuario.id, reporte_id))), 201


@bp.post("/reportes/<int:reporte_id>/whatsapp")
@requiere_permiso(Permiso.REGISTRAR_LLAMADAS)
def generar_mensaje_whatsapp(reporte_id: int):
    d = leer(MensajeWhatsAppIn)
    generado = contenedor().generar_mensaje_whatsapp().ejecutar(g.usuario.id, reporte_id, d.tutor_legal_id)
    return jsonify(mensaje_generado_a_dict(generado)), 201


@bp.post("/mensajes-whatsapp/<int:mensaje_id>/enviado")
@requiere_permiso(Permiso.REGISTRAR_LLAMADAS)
def marcar_mensaje_enviado(mensaje_id: int):
    mensaje = contenedor().marcar_mensaje_enviado().ejecutar(g.usuario.id, mensaje_id)
    return jsonify({"id": mensaje.id, "enviado_en": mensaje.enviado_en.isoformat() if mensaje.enviado_en else None})
