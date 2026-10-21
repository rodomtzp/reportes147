from typing import List, Optional

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, aliased

from app.application.dto.reportes import AccesoReportes, FiltroReportes
from app.application.ports.repositorios import (
    AdjuntoRepositorio, HistorialReporteRepositorio, ReporteRepositorio,
)
from app.domain.entities.adjunto import Adjunto
from app.domain.entities.historial_reporte import HistorialReporte
from app.domain.entities.reporte import Reporte
from app.domain.value_objects.estado_reporte import TipoEventoReporte
from app.infrastructure.persistence.models import (
    AdjuntoModel, EstudianteModel, FolioContadorModel, GrupoModel, HistorialReporteModel,
    InscripcionModel, IntentoLlamadaModel, ReporteModel,
)
from app.infrastructure.persistence.utils import flush_o_conflicto

_CAMPOS = (
    "folio", "incidente_id", "estudiante_id", "inscripcion_id", "creado_por", "tipo_incidencia_id",
    "descripcion", "descripcion_otro", "fecha_hora_incidente", "cancelado", "motivo_cancelacion",
    "cancelado_por", "cancelado_en", "creado_en", "ciclo_id", "cuenta_acumulacion",
)


def _reporte(m: ReporteModel) -> Reporte:
    return Reporte(id=m.id, gravedad=m.gravedad, estado=m.estado, **{c: getattr(m, c) for c in _CAMPOS})


def _patron(token: str) -> str:
    return "%" + token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


class ReporteRepositorioSQLAlchemy(ReporteRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, reporte_id: int) -> Optional[Reporte]:
        m = self._s.get(ReporteModel, reporte_id)
        return _reporte(m) if m else None

    def guardar(self, reporte: Reporte) -> Reporte:
        m = self._s.get(ReporteModel, reporte.id) if reporte.id else ReporteModel()
        for c in _CAMPOS:
            setattr(m, c, getattr(reporte, c))
        m.gravedad, m.estado = reporte.gravedad.value, reporte.estado.value
        self._s.add(m)
        flush_o_conflicto(self._s)
        reporte.id = m.id
        return reporte

    def _consulta(self, f: FiltroReportes):
        q = select(ReporteModel)
        a = f.acceso
        if not a.total:
            condiciones = []
            if a.creador_id is not None:
                condiciones.append(ReporteModel.creado_por == a.creador_id)
            if a.grupo_ids and a.periodo_id is not None:
                tutelados = (
                    select(InscripcionModel.estudiante_id)
                    .where(InscripcionModel.periodo_id == a.periodo_id, InscripcionModel.grupo_id.in_(a.grupo_ids))
                    .correlate(None)
                )
                condiciones.append(ReporteModel.estudiante_id.in_(tutelados))
            if not condiciones:
                return None
            q = q.where(or_(*condiciones))

        if f.reporte_id is not None:
            q = q.where(ReporteModel.id == f.reporte_id)
        if f.incidente_id is not None:
            q = q.where(ReporteModel.incidente_id == f.incidente_id)
        if f.estudiante_id is not None:
            q = q.where(ReporteModel.estudiante_id == f.estudiante_id)
        if f.ciclo_id is not None:
            q = q.where(ReporteModel.ciclo_id == f.ciclo_id)
        if f.solo_contables:
            q = q.where(ReporteModel.cancelado.is_(False), ReporteModel.cuenta_acumulacion.is_(True))
        if f.estado is not None:
            q = q.where(ReporteModel.estado == f.estado.value)
        if f.gravedad is not None:
            q = q.where(ReporteModel.gravedad == f.gravedad.value)
        if f.tipo_incidencia_id is not None:
            q = q.where(ReporteModel.tipo_incidencia_id == f.tipo_incidencia_id)
        if f.desde is not None:
            q = q.where(ReporteModel.fecha_hora_incidente >= f.desde)
        if f.hasta is not None:
            q = q.where(ReporteModel.fecha_hora_incidente <= f.hasta)
        if f.sin_llamada_efectiva:
            q = q.where(~exists().where(
                IntentoLlamadaModel.reporte_id == ReporteModel.id,
                IntentoLlamadaModel.estado.in_(["REALIZADA", "ATENDIDA"]),
            ))
        if not f.incluir_cancelados:
            q = q.where(ReporteModel.cancelado.is_(False))
        if f.grupo_id is not None or f.carrera_id is not None:
            insc = aliased(InscripcionModel)
            q = q.join(insc, insc.id == ReporteModel.inscripcion_id)
            if f.grupo_id is not None:
                q = q.where(insc.grupo_id == f.grupo_id)
            if f.carrera_id is not None:
                q = q.join(GrupoModel, GrupoModel.id == insc.grupo_id).where(GrupoModel.carrera_id == f.carrera_id)
        if f.texto and f.texto.split():
            q = q.join(EstudianteModel, EstudianteModel.id == ReporteModel.estudiante_id)
            for token in f.texto.split():
                p = _patron(token)
                q = q.where(or_(
                    ReporteModel.folio.ilike(p, escape="\\"),
                    EstudianteModel.numero_control.ilike(p, escape="\\"),
                    EstudianteModel.primer_apellido.ilike(p, escape="\\"),
                    EstudianteModel.segundo_apellido.ilike(p, escape="\\"),
                    EstudianteModel.nombres.ilike(p, escape="\\"),
                ))
        return q

    def listar(self, filtro: FiltroReportes) -> List[Reporte]:
        q = self._consulta(filtro)
        if q is None:
            return []
        q = q.order_by(ReporteModel.fecha_hora_incidente.desc(), ReporteModel.id.desc())
        q = q.limit(filtro.limite).offset(filtro.offset)
        return [_reporte(m) for m in self._s.scalars(q).all()]

    def es_visible(self, reporte_id: int, acceso: AccesoReportes) -> bool:
        return bool(self.listar(FiltroReportes(
            acceso=acceso, reporte_id=reporte_id, incluir_cancelados=True, limite=1)))

    def siguiente_numero_folio(self, anio: int) -> int:
        fila = self._s.get(FolioContadorModel, anio, with_for_update=True)  # bloquea la fila: sin folios repetidos
        if fila is None:
            fila = FolioContadorModel(anio=anio, ultimo=0)
            self._s.add(fila)
            flush_o_conflicto(self._s)
        fila.ultimo += 1
        self._s.flush()
        return fila.ultimo


def _evento(m: HistorialReporteModel) -> HistorialReporte:
    return HistorialReporte(
        id=m.id, reporte_id=m.reporte_id, tipo=TipoEventoReporte(m.tipo), usuario_id=m.usuario_id, fecha=m.fecha,
        campo=m.campo, valor_anterior=m.valor_anterior, valor_nuevo=m.valor_nuevo, comentario=m.comentario,
    )


class HistorialReporteRepositorioSQLAlchemy(HistorialReporteRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def agregar(self, evento: HistorialReporte) -> HistorialReporte:
        m = HistorialReporteModel(
            reporte_id=evento.reporte_id, tipo=TipoEventoReporte(evento.tipo).value, campo=evento.campo,
            valor_anterior=evento.valor_anterior, valor_nuevo=evento.valor_nuevo, comentario=evento.comentario,
            usuario_id=evento.usuario_id, fecha=evento.fecha,
        )
        self._s.add(m)
        flush_o_conflicto(self._s)
        evento.id = m.id
        return evento

    def listar_por_reporte(self, reporte_id: int) -> List[HistorialReporte]:
        q = select(HistorialReporteModel).where(HistorialReporteModel.reporte_id == reporte_id).order_by(HistorialReporteModel.id)
        return [_evento(m) for m in self._s.scalars(q).all()]


def _adjunto(m: AdjuntoModel) -> Adjunto:
    return Adjunto(id=m.id, reporte_id=m.reporte_id, nombre_original=m.nombre_original, tipo_mime=m.tipo_mime,
                   clave_almacen=m.clave_almacen, tamano=m.tamano, subido_por=m.subido_por, subido_en=m.subido_en)


class AdjuntoRepositorioSQLAlchemy(AdjuntoRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def guardar(self, adjunto: Adjunto) -> Adjunto:
        m = AdjuntoModel(
            reporte_id=adjunto.reporte_id, nombre_original=adjunto.nombre_original, tipo_mime=adjunto.tipo_mime,
            clave_almacen=adjunto.clave_almacen, tamano=adjunto.tamano, subido_por=adjunto.subido_por,
            subido_en=adjunto.subido_en,
        )
        self._s.add(m)
        flush_o_conflicto(self._s)
        adjunto.id = m.id
        return adjunto

    def obtener_por_id(self, adjunto_id: int) -> Optional[Adjunto]:
        m = self._s.get(AdjuntoModel, adjunto_id)
        return _adjunto(m) if m else None

    def listar_por_reporte(self, reporte_id: int) -> List[Adjunto]:
        q = select(AdjuntoModel).where(AdjuntoModel.reporte_id == reporte_id).order_by(AdjuntoModel.id)
        return [_adjunto(m) for m in self._s.scalars(q).all()]
