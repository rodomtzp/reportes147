from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.ports.repositorios import TipoIncidenciaRepositorio, TipoSancionRepositorio
from app.domain.entities.tipo_incidencia import TipoIncidencia
from app.domain.entities.tipo_sancion import TipoSancion
from app.infrastructure.persistence.models import TipoIncidenciaModel, TipoSancionModel
from app.infrastructure.persistence.utils import flush_o_conflicto


def _incidencia(m: TipoIncidenciaModel) -> TipoIncidencia:
    return TipoIncidencia(id=m.id, nombre=m.nombre, activo=m.activo, es_otro=m.es_otro)


def _sancion(m: TipoSancionModel) -> TipoSancion:
    return TipoSancion(id=m.id, nombre=m.nombre, requiere_dias=m.requiere_dias, activo=m.activo)


class TipoIncidenciaRepositorioSQLAlchemy(TipoIncidenciaRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, tipo_id: int) -> Optional[TipoIncidencia]:
        m = self._s.get(TipoIncidenciaModel, tipo_id)
        return _incidencia(m) if m else None

    def obtener_por_nombre(self, nombre: str) -> Optional[TipoIncidencia]:
        m = self._s.scalar(
            select(TipoIncidenciaModel).where(func.lower(TipoIncidenciaModel.nombre) == nombre.strip().lower())
        )
        return _incidencia(m) if m else None

    def listar(self, solo_activos: bool = False) -> List[TipoIncidencia]:
        q = select(TipoIncidenciaModel).order_by(TipoIncidenciaModel.id)
        if solo_activos:
            q = q.where(TipoIncidenciaModel.activo.is_(True))
        return [_incidencia(m) for m in self._s.scalars(q).all()]

    def guardar(self, tipo: TipoIncidencia) -> TipoIncidencia:
        m = self._s.get(TipoIncidenciaModel, tipo.id) if tipo.id else TipoIncidenciaModel()
        m.nombre, m.activo, m.es_otro = tipo.nombre, tipo.activo, tipo.es_otro
        self._s.add(m)
        flush_o_conflicto(self._s)
        tipo.id = m.id
        return tipo


class TipoSancionRepositorioSQLAlchemy(TipoSancionRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, tipo_id: int) -> Optional[TipoSancion]:
        m = self._s.get(TipoSancionModel, tipo_id)
        return _sancion(m) if m else None

    def obtener_por_nombre(self, nombre: str) -> Optional[TipoSancion]:
        m = self._s.scalar(
            select(TipoSancionModel).where(func.lower(TipoSancionModel.nombre) == nombre.strip().lower())
        )
        return _sancion(m) if m else None

    def listar(self, solo_activos: bool = False) -> List[TipoSancion]:
        q = select(TipoSancionModel).order_by(TipoSancionModel.id)
        if solo_activos:
            q = q.where(TipoSancionModel.activo.is_(True))
        return [_sancion(m) for m in self._s.scalars(q).all()]

    def guardar(self, tipo: TipoSancion) -> TipoSancion:
        m = self._s.get(TipoSancionModel, tipo.id) if tipo.id else TipoSancionModel()
        m.nombre, m.requiere_dias, m.activo = tipo.nombre, tipo.requiere_dias, tipo.activo
        self._s.add(m)
        flush_o_conflicto(self._s)
        tipo.id = m.id
        return tipo
