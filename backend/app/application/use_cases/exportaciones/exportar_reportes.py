"""Exportación a Excel de reportes por estudiante, grupo o carrera.

Cada quien exporta solo lo que puede ver (mismo `AccesoReportes` que la consulta): Orientación,
Subdirección y Dirección todo; el tutor, los estudiantes de sus grupos; el docente, lo que creó.
Los datos de contacto son opcionales y solo salen para quienes pueden verlos de ese estudiante.
Cada exportación queda en la bitácora.
"""
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Optional

from app.application.dto.exportaciones import (
    ALCANCES, MAX_FILAS_EXPORTACION, ArchivoExportado, FilaReporte, LibroReportes,
)
from app.application.dto.reportes import FiltroReportes
from app.application.ports.exportador import ExportadorExcelPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.bitacora.registro import registrar_exportacion
from app.application.use_cases.estudiantes._comun import grupo_y_carrera, mapas_academicos
from app.application.use_cases.estudiantes.acceso import grupos_tutelados
from app.application.use_cases.reportes._comun import acceso_de
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, PermisoDenegado, ReglaDeNegocioViolada
from app.domain.policies.politica_llamadas import resumen_estado_llamada
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.origen_sancion import OrigenSancion

ETIQUETA_ESTADO = {
    EstadoReporte.CREADO: "Creado",
    EstadoReporte.EN_REVISION_ORIENTACION: "En revisión por Orientación",
    EstadoReporte.ATENDIDO_SUBDIRECCION: "Atendido por Subdirección",
    EstadoReporte.SANCIONADO_CONCLUIDO: "Sancionado / Concluido",
}
ETIQUETA_GRAVEDAD = {"LEVE": "Leve", "MEDIA": "Media", "GRAVE": "Grave", "MUY_GRAVE": "Muy grave"}
ETIQUETA_LLAMADA = {"PENDIENTE": "Pendiente", "REALIZADA": "Realizada", "NO_CONTESTO": "No contestó", "ATENDIDA": "Atendida"}
ORDEN_GRAVEDAD = ["Leve", "Media", "Grave", "Muy grave"]


def _slug(texto: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_).strip("-").lower() or "reportes"


class ExportarReportes:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto, exportador: ExportadorExcelPuerto, plantel: str):
        self._uow, self._reloj, self._exportador, self._plantel = uow, reloj, exportador, plantel

    def ejecutar(self, actor: Usuario, alcance: str, objetivo_id: int, incluir_contacto: bool = False,
                 desde=None, hasta=None) -> ArchivoExportado:
        if alcance not in ALCANCES:
            raise ReglaDeNegocioViolada("El alcance debe ser estudiante, grupo o carrera.")
        with self._uow as uow:
            acceso = acceso_de(uow, actor)
            if acceso.sin_acceso:
                raise PermisoDenegado("No tienes permiso para exportar reportes.")
            contacto_total = tiene_permiso(actor.roles, Permiso.VER_DATOS_CONTACTO)
            tutelados = grupos_tutelados(uow, actor)
            if incluir_contacto and not contacto_total and not tutelados:
                raise PermisoDenegado("No tienes permiso para ver datos de contacto.")

            grupos, carreras = mapas_academicos(uow)
            filtro, descripcion, ids = self._filtro(uow, alcance, objetivo_id, acceso, grupos, carreras, desde, hasta)
            reportes = uow.reportes.listar(FiltroReportes(
                **filtro, acceso=acceso, incluir_cancelados=True, desde=desde, hasta=hasta,
                limite=MAX_FILAS_EXPORTACION + 1))
            if len(reportes) > MAX_FILAS_EXPORTACION:
                raise ReglaDeNegocioViolada(
                    f"La exportación supera {MAX_FILAS_EXPORTACION} reportes. Acota el rango de fechas.")

            filas = self._filas(uow, reportes, grupos, carreras, incluir_contacto, contacto_total, tutelados)
            libro = LibroReportes(
                titulo="Reportes disciplinarios", subtitulo=descripcion + self._texto_fechas(desde, hasta),
                plantel=self._plantel, generado_por=actor.nombre, generado_en=self._reloj.ahora(),
                incluye_contacto=any(f.telefono_tutor or f.domicilio or f.tutor_legal for f in filas),
                filas=filas, **self._resumen(filas),
            )
            contenido = self._exportador.generar(libro)
            registrar_exportacion(
                uow, self._reloj, actor.id, f"Excel por {alcance}: {descripcion}", len(filas), libro.incluye_contacto,
                **ids)
            uow.commit()
            nombre = f"reportes_{alcance}_{_slug(descripcion.split(':', 1)[-1])}_{libro.generado_en:%Y%m%d}.xlsx"
            return ArchivoExportado(nombre, contenido, len(filas))

    # ---- piezas ----
    def _filtro(self, uow, alcance, objetivo_id, acceso, grupos, carreras, desde, hasta):
        if alcance == "estudiante":
            e = uow.estudiantes.obtener_por_id(objetivo_id)
            if e is None:
                raise NoEncontrado("Estudiante no encontrado.")
            return ({"estudiante_id": e.id}, f"Estudiante: {e.nombre_completo} ({e.numero_control})",
                    {"estudiante_id": e.id})
        if alcance == "grupo":
            g = grupos.get(objetivo_id)
            if g is None:
                raise NoEncontrado("Grupo no encontrado.")
            carrera = carreras.get(g.carrera_id)
            return ({"grupo_id": g.id}, f"Grupo: {g.clave}" + (f" — {carrera.nombre}" if carrera else ""),
                    {"grupo_id": g.id})
        c = carreras.get(objetivo_id)
        if c is None:
            raise NoEncontrado("Carrera no encontrada.")
        return {"carrera_id": c.id}, f"Carrera: {c.nombre}", {"carrera_id": c.id}

    @staticmethod
    def _texto_fechas(desde, hasta) -> str:
        if not desde and not hasta:
            return ""
        d = f"{desde:%d/%m/%Y}" if desde else "inicio"
        h = f"{hasta:%d/%m/%Y}" if hasta else "hoy"
        return f" · Del {d} al {h}"

    def _filas(self, uow, reportes, grupos, carreras, incluir_contacto, contacto_total, tutelados) -> List[FilaReporte]:
        if not reportes:
            return []
        estudiantes = uow.estudiantes.obtener_por_ids({r.estudiante_id for r in reportes})
        inscripciones = uow.inscripciones.obtener_por_ids({r.inscripcion_id for r in reportes})
        autores = uow.usuarios.obtener_por_ids({r.creado_por for r in reportes})
        tipos = {t.id: t for t in uow.tipos_incidencia.listar()}
        tipos_sancion = {t.id: t for t in uow.tipos_sancion.listar()}
        intentos = uow.llamadas.listar_por_reportes([r.id for r in reportes])
        periodo = uow.periodos.obtener_vigente()
        actuales = (uow.inscripciones.obtener_de_estudiantes(list(estudiantes), periodo.id) if periodo else {})
        por_ciclo: Dict[int, Optional[object]] = {}
        tutores_cache: Dict[int, list] = {}

        def etiqueta_sancion(s) -> str:
            t = tipos_sancion.get(s.tipo_sancion_id)
            texto = t.nombre if t else "Sanción"
            if s.dias:
                texto += f" ({s.dias} días)"
            return texto + (" — por acumulación" if s.origen == OrigenSancion.ACUMULACION else " — directa")

        def sancion_de(r) -> Optional[str]:
            s = uow.sanciones.obtener_por_reporte(r.id)
            if s is None and r.estado == EstadoReporte.SANCIONADO_CONCLUIDO and r.ciclo_id and r.es_contable:
                if r.ciclo_id not in por_ciclo:
                    por_ciclo[r.ciclo_id] = uow.sanciones.obtener_por_ciclo(r.ciclo_id)
                s = por_ciclo[r.ciclo_id]
            return etiqueta_sancion(s) if s else None

        filas = []
        for r in reportes:
            e = estudiantes.get(r.estudiante_id)
            insc = inscripciones.get(r.inscripcion_id)
            clave, carrera = grupo_y_carrera(grupos, carreras, insc.grupo_id if insc else None)
            tipo = tipos.get(r.tipo_incidencia_id)
            descripcion = r.descripcion + (f" (Otro: {r.descripcion_otro})" if r.descripcion_otro else "")
            contacto = {}
            ver = incluir_contacto and e is not None and (
                contacto_total or (e.id in actuales and actuales[e.id].grupo_id in tutelados))
            if ver:
                if e.id not in tutores_cache:
                    tutores_cache[e.id] = uow.tutores_legales.listar_por_estudiante(e.id)
                tutores = tutores_cache[e.id]
                principal = next((t for t in tutores if t.es_principal), tutores[0] if tutores else None)
                domicilio = ", ".join(p for p in (
                    " ".join(p for p in (e.calle, e.numero) if p), e.colonia, e.ciudad) if p) or None
                contacto = dict(
                    tutor_legal=(f"{principal.nombre} ({principal.parentesco})" if principal and principal.parentesco
                                 else (principal.nombre if principal else None)),
                    telefono_tutor=principal.telefono if principal else None,
                    correo_tutor=principal.correo if principal else None, domicilio=domicilio)
            filas.append(FilaReporte(
                folio=r.folio or "", fecha_incidente=self._reloj.localizar(r.fecha_hora_incidente),
                numero_control=e.numero_control if e else "?", estudiante=e.nombre_completo if e else "?",
                grupo=clave, carrera=carrera, tipo_incidencia=tipo.nombre if tipo else "?", descripcion=descripcion,
                gravedad=ETIQUETA_GRAVEDAD[r.gravedad.value], estado=ETIQUETA_ESTADO[r.estado], cancelado=r.cancelado,
                motivo_cancelacion=r.motivo_cancelacion, cuenta_acumulacion=r.es_contable,
                creado_por=autores[r.creado_por].nombre if r.creado_por in autores else "?",
                llamada=ETIQUETA_LLAMADA[resumen_estado_llamada([i.estado for i in intentos.get(r.id, [])]).value],
                sancion=sancion_de(r), **contacto,
            ))
        return filas

    @staticmethod
    def _resumen(filas: List[FilaReporte]) -> dict:
        vigentes = [f for f in filas if not f.cancelado]
        gravedad = Counter(f.gravedad for f in vigentes)
        estado = Counter("Cancelado" if f.cancelado else f.estado for f in filas)
        sanciones = Counter(f.sancion for f in vigentes if f.sancion)
        return dict(
            por_gravedad=[(g, gravedad.get(g, 0)) for g in ORDEN_GRAVEDAD],
            por_estado=sorted(estado.items()),
            por_sancion=sorted(sanciones.items()),
            sin_llamada_efectiva=sum(1 for f in vigentes if f.llamada in ("Pendiente", "No contestó")),
        )
