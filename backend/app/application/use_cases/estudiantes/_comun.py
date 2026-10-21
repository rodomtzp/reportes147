"""Utilidades compartidas por los casos de uso de estudiantes."""
from typing import Dict, List, Optional

from app.application.dto.estudiantes import EstudianteDetalle, InscripcionDetalle
from app.domain.entities.estudiante import Estudiante
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.exceptions import ReglaDeNegocioViolada


def periodo_vigente_o_error(uow):
    periodo = uow.periodos.obtener_vigente()
    if periodo is None:
        raise ReglaDeNegocioViolada("No hay un periodo escolar vigente. Define uno en Periodos.")
    return periodo


def grupo_activo_o_error(uow, grupo_id: int):
    from app.domain.exceptions import NoEncontrado

    grupo = uow.grupos.obtener_por_id(grupo_id)
    if grupo is None:
        raise NoEncontrado("Grupo no encontrado.")
    if not grupo.activo:
        raise ReglaDeNegocioViolada("El grupo está desactivado.")
    return grupo


def mapas_academicos(uow):
    """Grupos y carreras por id (son catálogos pequeños)."""
    grupos = {g.id: g for g in uow.grupos.listar()}
    carreras = {c.id: c for c in uow.carreras.listar()}
    return grupos, carreras


def grupo_y_carrera(grupos, carreras, grupo_id: Optional[int]):
    g = grupos.get(grupo_id) if grupo_id else None
    c = carreras.get(g.carrera_id) if g else None
    return (g.clave if g else None), (c.nombre if c else None)


def armar_detalle(uow, estudiante: Estudiante) -> EstudianteDetalle:
    grupos, carreras = mapas_academicos(uow)
    periodos = {p.id: p for p in uow.periodos.listar()}
    vigente = uow.periodos.obtener_vigente()
    historial: List[InscripcionDetalle] = []
    actual_gid: Optional[int] = None
    for insc in uow.inscripciones.listar_por_estudiante(estudiante.id):
        g = grupos[insc.grupo_id]
        historial.append(InscripcionDetalle(
            inscripcion=insc,
            periodo_nombre=periodos[insc.periodo_id].nombre,
            grupo_clave=g.clave,
            semestre=g.semestre,
            carrera_nombre=carreras[g.carrera_id].nombre,
        ))
        if vigente and insc.periodo_id == vigente.id:
            actual_gid = insc.grupo_id
    clave, carrera = grupo_y_carrera(grupos, carreras, actual_gid)
    return EstudianteDetalle(
        estudiante=estudiante,
        tutores_legales=uow.tutores_legales.listar_por_estudiante(estudiante.id),
        inscripciones=historial,
        grupo_actual=clave,
        carrera_actual=carrera,
    )


def asegurar_un_principal(tutores: List[TutorLegal], preferido: Optional[TutorLegal] = None) -> None:
    """Deja exactamente un tutor principal (el preferido, o el primero si ninguno lo es)."""
    if not tutores:
        return
    if preferido is not None and preferido.es_principal:
        elegido = preferido
    else:
        elegido = next((t for t in tutores if t.es_principal), tutores[0])
    for t in tutores:
        t.es_principal = t is elegido
