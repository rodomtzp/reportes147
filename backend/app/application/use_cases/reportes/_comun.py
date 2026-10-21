"""Utilidades compartidas por los casos de uso de reportes."""
from typing import Iterable, List, Optional

from app.application.dto.reportes import (
    AccesoReportes, AlertaReporte, EventoDetalle, FiltroReportes, ReporteDetalle, ReporteListado,
)
from app.application.use_cases.estudiantes._comun import grupo_y_carrera, mapas_academicos
from app.application.use_cases.llamadas._comun import llamadas_detalle, mensajes_detalle
from app.application.use_cases.sanciones.vistas import resumen_acumulacion, sancion_de_reporte
from app.application.use_cases.estudiantes.acceso import grupos_tutelados
from app.domain.entities.historial_reporte import HistorialReporte
from app.domain.entities.reporte import Reporte
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, PermisoDenegado
from app.domain.policies.politica_llamadas import resumen_estado_llamada
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_reporte import TipoEventoReporte


def acceso_de(uow, actor: Usuario) -> AccesoReportes:
    """Orientación/Subdirección/Dirección ven todo; el docente, lo que creó; el tutor, a los
    estudiantes de sus grupos (todo su historial). Los prefectos no consultan reportes."""
    if tiene_permiso(actor.roles, Permiso.VER_TODOS_LOS_REPORTES):
        return AccesoReportes(total=True)
    periodo = uow.periodos.obtener_vigente()
    return AccesoReportes(
        creador_id=actor.id if tiene_permiso(actor.roles, Permiso.VER_REPORTES_PROPIOS) else None,
        grupo_ids=sorted(grupos_tutelados(uow, actor)),
        periodo_id=periodo.id if periodo else None,
    )


def cargar_reporte(uow, reporte_id: int) -> Reporte:
    reporte = uow.reportes.obtener_por_id(reporte_id)
    if reporte is None:
        raise NoEncontrado("Reporte no encontrado.")
    return reporte


def cargar_visible(uow, actor: Usuario, reporte_id: int):
    reporte = cargar_reporte(uow, reporte_id)
    acceso = acceso_de(uow, actor)
    if acceso.sin_acceso or not uow.reportes.es_visible(reporte_id, acceso):
        raise PermisoDenegado("No tienes acceso a este reporte.")
    return reporte, acceso


def registrar(uow, reporte_id: int, tipo: TipoEventoReporte, usuario_id: int, fecha, **datos) -> None:
    uow.historial_reportes.agregar(
        HistorialReporte(reporte_id=reporte_id, tipo=tipo, usuario_id=usuario_id, fecha=fecha, **datos)
    )


def enriquecer(uow, reportes: Iterable[Reporte]) -> List[ReporteListado]:
    reportes = list(reportes)
    if not reportes:
        return []
    estudiantes = uow.estudiantes.obtener_por_ids({r.estudiante_id for r in reportes})
    inscripciones = uow.inscripciones.obtener_por_ids({r.inscripcion_id for r in reportes})
    usuarios = uow.usuarios.obtener_por_ids({r.creado_por for r in reportes})
    tipos = {t.id: t for t in uow.tipos_incidencia.listar()}
    intentos = uow.llamadas.listar_por_reportes([r.id for r in reportes])
    grupos, carreras = mapas_academicos(uow)
    salida = []
    for r in reportes:
        e = estudiantes.get(r.estudiante_id)
        insc = inscripciones.get(r.inscripcion_id)
        clave, carrera = grupo_y_carrera(grupos, carreras, insc.grupo_id if insc else None)
        tipo = tipos.get(r.tipo_incidencia_id)
        autor = usuarios.get(r.creado_por)
        salida.append(ReporteListado(
            reporte=r,
            estudiante=e.nombre_completo if e else "?",
            numero_control=e.numero_control if e else "?",
            grupo_clave=clave,
            carrera_nombre=carrera,
            tipo_incidencia=(tipo.nombre if tipo else "?"),
            creado_por_nombre=autor.nombre if autor else "?",
            estado_llamada=resumen_estado_llamada([i.estado for i in intentos.get(r.id, [])]).value,
        ))
    return salida


def detalle_de(uow, actor_acceso: AccesoReportes, reporte: Reporte, incluir_seguimiento: bool = False,
               incluir_acumulacion: bool = False) -> ReporteDetalle:
    listado = enriquecer(uow, [reporte])[0]
    eventos = uow.historial_reportes.listar_por_reporte(reporte.id)
    nombres = uow.usuarios.obtener_por_ids({e.usuario_id for e in eventos} | ({reporte.cancelado_por} if reporte.cancelado_por else set()))
    hermanos = uow.reportes.listar(FiltroReportes(
        acceso=actor_acceso, incidente_id=reporte.incidente_id, incluir_cancelados=True, limite=100))
    return ReporteDetalle(
        listado=listado,
        adjuntos=uow.adjuntos.listar_por_reporte(reporte.id),
        historial=[EventoDetalle(e, nombres[e.usuario_id].nombre if e.usuario_id in nombres else "?") for e in eventos],
        relacionados=enriquecer(uow, [h for h in hermanos if h.id != reporte.id]),
        cancelado_por_nombre=nombres[reporte.cancelado_por].nombre if reporte.cancelado_por in nombres else None,
        llamadas=llamadas_detalle(uow, reporte.id) if incluir_seguimiento else None,
        mensajes=mensajes_detalle(uow, reporte.id) if incluir_seguimiento else None,
        sancion=sancion_de_reporte(uow, reporte, con_observaciones=incluir_acumulacion),
        acumulacion=resumen_acumulacion(uow, reporte.estudiante_id) if incluir_acumulacion else None,
    )


def alertas_de(uow, reportes: Iterable[Reporte]) -> List[AlertaReporte]:
    return [
        AlertaReporte(l.reporte.id, l.reporte.estudiante_id, l.reporte.folio, l.estudiante, l.grupo_clave, l.reporte.gravedad, l.tipo_incidencia)
        for l in enriquecer(uow, reportes)
    ]
