from flask import Blueprint, Response, g, jsonify, request

from app.application.dto.estudiantes import MAX_BYTES_IMPORTACION as MAX_BYTES
from app.application.use_cases.estudiantes.plantilla import plantilla_importacion_csv
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_permisos import Permiso
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
from app.interfaces.api.helpers import arg_enum, contenedor, leer, parametros_cambiados
from app.interfaces.api.middlewares.auth import requiere_autenticacion, requiere_permiso
from app.interfaces.api.schemas.estudiantes import (
    AvanceSemestreIn, CambiarGrupoIn, EstudianteActualizarIn, EstudianteCrearIn,
    TutorLegalActualizarIn, TutorLegalIn,
)
from app.interfaces.api.serializadores import (
    avance_a_dict, estudiante_detalle_a_dict, estudiante_listado_a_dict, estudiante_resumen_a_dict,
    importacion_a_dict, tutor_legal_a_dict,
)

bp = Blueprint("estudiantes", __name__)
GESTIONAR = Permiso.GESTIONAR_ESTUDIANTES


@bp.get("/estudiantes/buscar")
@requiere_permiso(Permiso.CREAR_REPORTE)
def buscar_estudiantes():
    """Buscador para crear reportes: solo datos mínimos (sin teléfonos ni dirección)."""
    resultados = contenedor().buscar_estudiantes().ejecutar(request.args.get("q", ""))
    return jsonify([estudiante_resumen_a_dict(r) for r in resultados])


@bp.get("/estudiantes/plantilla")
@requiere_permiso(Permiso.IMPORTAR_ESTUDIANTES)
def plantilla_importacion():
    contenido = "\ufeff" + plantilla_importacion_csv()  # BOM: Excel respeta los acentos
    return Response(
        contenido, mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="plantilla_estudiantes.csv"'},
    )


@bp.get("/estudiantes")
@requiere_autenticacion
def listar_estudiantes():
    items = contenedor().listar_estudiantes().ejecutar(
        g.usuario,
        texto=request.args.get("q"),
        estatus=arg_enum("estatus", EstatusEstudiante),
        grupo_id=request.args.get("grupo_id", type=int),
        carrera_id=request.args.get("carrera_id", type=int),
        limite=request.args.get("limite", default=200, type=int),
        offset=max(0, request.args.get("offset", default=0, type=int)),
    )
    return jsonify([estudiante_listado_a_dict(i) for i in items])


@bp.get("/estudiantes/<int:estudiante_id>")
@requiere_autenticacion
def obtener_estudiante(estudiante_id: int):
    return jsonify(estudiante_detalle_a_dict(contenedor().obtener_estudiante().ejecutar(g.usuario, estudiante_id)))


@bp.post("/estudiantes")
@requiere_permiso(GESTIONAR)
def crear_estudiante():
    d = leer(EstudianteCrearIn)
    datos = d.model_dump(exclude={"grupo_id", "tutores"})
    tutores = [t.model_dump() for t in d.tutores]
    detalle = contenedor().crear_estudiante().ejecutar(d.grupo_id, tutores, **datos)
    return jsonify(estudiante_detalle_a_dict(detalle)), 201


@bp.patch("/estudiantes/<int:estudiante_id>")
@requiere_permiso(GESTIONAR)
def actualizar_estudiante(estudiante_id: int):
    cambios = parametros_cambiados(leer(EstudianteActualizarIn))
    return jsonify(estudiante_detalle_a_dict(contenedor().actualizar_estudiante().ejecutar(estudiante_id, **cambios)))


@bp.post("/estudiantes/<int:estudiante_id>/grupo")
@requiere_permiso(GESTIONAR)
def cambiar_grupo_estudiante(estudiante_id: int):
    d = leer(CambiarGrupoIn)
    return jsonify(estudiante_detalle_a_dict(contenedor().cambiar_grupo_estudiante().ejecutar(estudiante_id, d.grupo_id)))


# ---- Padres o tutores legales ----
@bp.post("/estudiantes/<int:estudiante_id>/tutores-legales")
@requiere_permiso(GESTIONAR)
def agregar_tutor_legal(estudiante_id: int):
    datos = leer(TutorLegalIn).model_dump()
    tutores = contenedor().agregar_tutor_legal().ejecutar(estudiante_id, **datos)
    return jsonify([tutor_legal_a_dict(t) for t in tutores]), 201


@bp.patch("/tutores-legales/<int:tutor_id>")
@requiere_permiso(GESTIONAR)
def actualizar_tutor_legal(tutor_id: int):
    cambios = parametros_cambiados(leer(TutorLegalActualizarIn))
    tutores = contenedor().actualizar_tutor_legal().ejecutar(tutor_id, **cambios)
    return jsonify([tutor_legal_a_dict(t) for t in tutores])


@bp.delete("/tutores-legales/<int:tutor_id>")
@requiere_permiso(GESTIONAR)
def eliminar_tutor_legal(tutor_id: int):
    tutores = contenedor().eliminar_tutor_legal().ejecutar(tutor_id)
    return jsonify([tutor_legal_a_dict(t) for t in tutores])


# ---- Importación y avance de semestre (Administrador) ----
@bp.post("/estudiantes/importar")
@requiere_permiso(Permiso.IMPORTAR_ESTUDIANTES)
def importar_estudiantes():
    if (request.content_length or 0) > MAX_BYTES + 4096:
        raise ReglaDeNegocioViolada("El archivo excede el tamaño máximo de 2 MB.")
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        raise ReglaDeNegocioViolada("Adjunta un archivo .csv o .xlsx en el campo 'archivo'.")
    resultado = contenedor().importar_estudiantes().ejecutar(archivo.read(MAX_BYTES + 1), archivo.filename)
    return jsonify(importacion_a_dict(resultado))


@bp.post("/estudiantes/avance-semestre")
@requiere_permiso(Permiso.AVANZAR_SEMESTRE)
def avanzar_semestre():
    d = leer(AvanceSemestreIn)
    excepciones = {e.estudiante_id: e.accion for e in d.excepciones}
    resumen = contenedor().avanzar_semestre().ejecutar(
        d.periodo_origen_id, d.periodo_destino_id, excepciones, simular=d.simular
    )
    return jsonify(avance_a_dict(resumen))
