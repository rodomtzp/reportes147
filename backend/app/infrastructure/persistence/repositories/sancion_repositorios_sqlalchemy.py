from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.ports.repositorios import CicloRepositorio, NotificacionRepositorio, SancionRepositorio
from app.domain.entities.ciclo_acumulacion import CicloAcumulacion
from app.domain.entities.notificacion import Notificacion
from app.domain.entities.sancion import Sancion
from app.infrastructure.persistence.models import CicloAcumulacionModel, NotificacionModel, SancionModel
from app.infrastructure.persistence.utils import flush_o_conflicto


def _ciclo(m: CicloAcumulacionModel) -> CicloAcumulacion:
    return CicloAcumulacion(id=m.id, estudiante_id=m.estudiante_id, numero=m.numero, fecha_inicio=m.fecha_inicio,
                            abierto=m.abierto, fecha_cierre=m.fecha_cierre)


class CicloRepositorioSQLAlchemy(CicloRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_abierto(self, estudiante_id: int) -> Optional[CicloAcumulacion]:
        m = self._s.scalar(select(CicloAcumulacionModel).where(
            CicloAcumulacionModel.estudiante_id == estudiante_id, CicloAcumulacionModel.abierto.is_(True)))
        return _ciclo(m) if m else None

    def listar_por_estudiante(self, estudiante_id: int) -> List[CicloAcumulacion]:
        q = select(CicloAcumulacionModel).where(CicloAcumulacionModel.estudiante_id == estudiante_id).order_by(CicloAcumulacionModel.numero)
        return [_ciclo(m) for m in self._s.scalars(q).all()]

    def siguiente_numero(self, estudiante_id: int) -> int:
        ultimo = self._s.scalar(select(func.max(CicloAcumulacionModel.numero)).where(CicloAcumulacionModel.estudiante_id == estudiante_id))
        return (ultimo or 0) + 1

    def guardar(self, ciclo: CicloAcumulacion) -> CicloAcumulacion:
        m = self._s.get(CicloAcumulacionModel, ciclo.id) if ciclo.id else CicloAcumulacionModel()
        m.estudiante_id, m.numero, m.fecha_inicio = ciclo.estudiante_id, ciclo.numero, ciclo.fecha_inicio
        m.abierto, m.fecha_cierre = ciclo.abierto, ciclo.fecha_cierre
        self._s.add(m)
        flush_o_conflicto(self._s)
        ciclo.id = m.id
        return ciclo


_CAMPOS_SANCION = ("tipo_sancion_id", "estudiante_id", "reporte_id", "ciclo_id", "dias", "observaciones", "aplicada_por", "aplicada_en")


def _sancion(m: SancionModel) -> Sancion:
    return Sancion(id=m.id, origen=m.origen, **{c: getattr(m, c) for c in _CAMPOS_SANCION})


class SancionRepositorioSQLAlchemy(SancionRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def guardar(self, sancion: Sancion) -> Sancion:
        m = self._s.get(SancionModel, sancion.id) if sancion.id else SancionModel()
        for c in _CAMPOS_SANCION:
            setattr(m, c, getattr(sancion, c))
        m.origen = sancion.origen.value
        self._s.add(m)
        flush_o_conflicto(self._s)
        sancion.id = m.id
        return sancion

    def obtener_por_reporte(self, reporte_id: int) -> Optional[Sancion]:
        m = self._s.scalar(select(SancionModel).where(SancionModel.reporte_id == reporte_id))
        return _sancion(m) if m else None

    def obtener_por_ciclo(self, ciclo_id: int) -> Optional[Sancion]:
        m = self._s.scalar(select(SancionModel).where(SancionModel.ciclo_id == ciclo_id))
        return _sancion(m) if m else None

    def listar_por_estudiante(self, estudiante_id: int) -> List[Sancion]:
        q = select(SancionModel).where(SancionModel.estudiante_id == estudiante_id).order_by(SancionModel.aplicada_en.desc(), SancionModel.id.desc())
        return [_sancion(m) for m in self._s.scalars(q).all()]


_CAMPOS_NOTIF = ("tipo", "titulo", "mensaje", "rol_destino", "reporte_id", "estudiante_id", "creada_en",
                 "correo_enviado", "correo_error", "atendida_por", "atendida_en")


def _notificacion(m: NotificacionModel) -> Notificacion:
    return Notificacion(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_NOTIF})


class NotificacionRepositorioSQLAlchemy(NotificacionRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def guardar(self, notificacion: Notificacion) -> Notificacion:
        m = self._s.get(NotificacionModel, notificacion.id) if notificacion.id else NotificacionModel()
        for c in _CAMPOS_NOTIF:
            setattr(m, c, getattr(notificacion, c))
        self._s.add(m)
        flush_o_conflicto(self._s)
        notificacion.id = m.id
        return notificacion

    def obtener_por_id(self, notificacion_id: int) -> Optional[Notificacion]:
        m = self._s.get(NotificacionModel, notificacion_id)
        return _notificacion(m) if m else None

    def listar(self, rol_destino: str, solo_pendientes: bool = False, limite: int = 100, offset: int = 0) -> List[Notificacion]:
        q = select(NotificacionModel).where(NotificacionModel.rol_destino == rol_destino)
        if solo_pendientes:
            q = q.where(NotificacionModel.atendida_en.is_(None))
        q = q.order_by(NotificacionModel.creada_en.desc(), NotificacionModel.id.desc()).limit(limite).offset(offset)
        return [_notificacion(m) for m in self._s.scalars(q).all()]

    def contar_pendientes(self, rol_destino: str) -> int:
        q = select(func.count(NotificacionModel.id)).where(
            NotificacionModel.rol_destino == rol_destino, NotificacionModel.atendida_en.is_(None))
        return int(self._s.scalar(q) or 0)
