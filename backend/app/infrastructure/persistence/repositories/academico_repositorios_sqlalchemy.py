from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.ports.repositorios import (
    AsignacionTutorRepositorio,
    CarreraRepositorio,
    GrupoRepositorio,
    PeriodoRepositorio,
)
from app.domain.entities.asignacion_tutor import AsignacionTutor
from app.domain.entities.carrera import Carrera
from app.domain.entities.grupo import Grupo
from app.domain.entities.periodo_escolar import PeriodoEscolar
from app.infrastructure.persistence.models import (
    AsignacionTutorModel, CarreraModel, GrupoModel, PeriodoEscolarModel,
)
from app.infrastructure.persistence.utils import flush_o_conflicto


# ---------------- Carrera ----------------
def _carrera(m: CarreraModel) -> Carrera:
    return Carrera(id=m.id, nombre=m.nombre, clave=m.clave, activa=m.activa)


class CarreraRepositorioSQLAlchemy(CarreraRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, carrera_id: int) -> Optional[Carrera]:
        m = self._s.get(CarreraModel, carrera_id)
        return _carrera(m) if m else None

    def obtener_por_clave(self, clave: str) -> Optional[Carrera]:
        m = self._s.scalar(select(CarreraModel).where(CarreraModel.clave == clave.strip().upper()))
        return _carrera(m) if m else None

    def listar(self, solo_activas: bool = False) -> List[Carrera]:
        q = select(CarreraModel).order_by(CarreraModel.nombre)
        if solo_activas:
            q = q.where(CarreraModel.activa.is_(True))
        return [_carrera(m) for m in self._s.scalars(q).all()]

    def guardar(self, carrera: Carrera) -> Carrera:
        m = self._s.get(CarreraModel, carrera.id) if carrera.id else CarreraModel()
        m.nombre, m.clave, m.activa = carrera.nombre, carrera.clave, carrera.activa
        self._s.add(m)
        flush_o_conflicto(self._s)
        carrera.id = m.id
        return carrera


# ---------------- Grupo ----------------
def _grupo(m: GrupoModel) -> Grupo:
    return Grupo(id=m.id, carrera_id=m.carrera_id, semestre=m.semestre, letra=m.letra, activo=m.activo)


class GrupoRepositorioSQLAlchemy(GrupoRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, grupo_id: int) -> Optional[Grupo]:
        m = self._s.get(GrupoModel, grupo_id)
        return _grupo(m) if m else None

    def obtener_por_semestre_y_letra(self, semestre: int, letra: str) -> Optional[Grupo]:
        m = self._s.scalar(
            select(GrupoModel).where(GrupoModel.semestre == semestre, GrupoModel.letra == letra.strip().upper())
        )
        return _grupo(m) if m else None

    def listar(self, carrera_id=None, semestre=None, solo_activos=False) -> List[Grupo]:
        q = select(GrupoModel).order_by(GrupoModel.semestre, GrupoModel.letra)
        if carrera_id is not None:
            q = q.where(GrupoModel.carrera_id == carrera_id)
        if semestre is not None:
            q = q.where(GrupoModel.semestre == semestre)
        if solo_activos:
            q = q.where(GrupoModel.activo.is_(True))
        return [_grupo(m) for m in self._s.scalars(q).all()]

    def guardar(self, grupo: Grupo) -> Grupo:
        m = self._s.get(GrupoModel, grupo.id) if grupo.id else GrupoModel()
        m.carrera_id, m.semestre, m.letra, m.activo = grupo.carrera_id, grupo.semestre, grupo.letra, grupo.activo
        self._s.add(m)
        flush_o_conflicto(self._s)
        grupo.id = m.id
        return grupo


# ---------------- Periodo ----------------
def _periodo(m: PeriodoEscolarModel) -> PeriodoEscolar:
    return PeriodoEscolar(
        id=m.id, nombre=m.nombre, fecha_inicio=m.fecha_inicio, fecha_fin=m.fecha_fin, vigente=m.vigente
    )


class PeriodoRepositorioSQLAlchemy(PeriodoRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, periodo_id: int) -> Optional[PeriodoEscolar]:
        m = self._s.get(PeriodoEscolarModel, periodo_id)
        return _periodo(m) if m else None

    def obtener_por_nombre(self, nombre: str) -> Optional[PeriodoEscolar]:
        m = self._s.scalar(select(PeriodoEscolarModel).where(PeriodoEscolarModel.nombre == nombre.strip()))
        return _periodo(m) if m else None

    def obtener_vigente(self) -> Optional[PeriodoEscolar]:
        m = self._s.scalar(select(PeriodoEscolarModel).where(PeriodoEscolarModel.vigente.is_(True)))
        return _periodo(m) if m else None

    def listar(self) -> List[PeriodoEscolar]:
        q = select(PeriodoEscolarModel).order_by(PeriodoEscolarModel.fecha_inicio.desc())
        return [_periodo(m) for m in self._s.scalars(q).all()]

    def desactivar_vigentes(self) -> None:
        self._s.execute(
            update(PeriodoEscolarModel)
            .where(PeriodoEscolarModel.vigente.is_(True))
            .values(vigente=False)
            .execution_options(synchronize_session="fetch")
        )

    def guardar(self, periodo: PeriodoEscolar) -> PeriodoEscolar:
        m = self._s.get(PeriodoEscolarModel, periodo.id) if periodo.id else PeriodoEscolarModel()
        m.nombre, m.fecha_inicio, m.fecha_fin, m.vigente = (
            periodo.nombre, periodo.fecha_inicio, periodo.fecha_fin, periodo.vigente,
        )
        self._s.add(m)
        flush_o_conflicto(self._s)
        periodo.id = m.id
        return periodo


# ---------------- Asignación de tutor ----------------
def _asignacion(m: AsignacionTutorModel) -> AsignacionTutor:
    return AsignacionTutor(id=m.id, usuario_id=m.usuario_id, grupo_id=m.grupo_id, periodo_id=m.periodo_id)


class AsignacionTutorRepositorioSQLAlchemy(AsignacionTutorRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, asignacion_id: int) -> Optional[AsignacionTutor]:
        m = self._s.get(AsignacionTutorModel, asignacion_id)
        return _asignacion(m) if m else None

    def obtener_por_grupo_y_periodo(self, grupo_id: int, periodo_id: int) -> Optional[AsignacionTutor]:
        m = self._s.scalar(
            select(AsignacionTutorModel).where(
                AsignacionTutorModel.grupo_id == grupo_id, AsignacionTutorModel.periodo_id == periodo_id
            )
        )
        return _asignacion(m) if m else None

    def listar(self, periodo_id=None, grupo_id=None, usuario_id=None) -> List[AsignacionTutor]:
        q = select(AsignacionTutorModel).order_by(AsignacionTutorModel.id)
        if periodo_id is not None:
            q = q.where(AsignacionTutorModel.periodo_id == periodo_id)
        if grupo_id is not None:
            q = q.where(AsignacionTutorModel.grupo_id == grupo_id)
        if usuario_id is not None:
            q = q.where(AsignacionTutorModel.usuario_id == usuario_id)
        return [_asignacion(m) for m in self._s.scalars(q).all()]

    def guardar(self, asignacion: AsignacionTutor) -> AsignacionTutor:
        m = self._s.get(AsignacionTutorModel, asignacion.id) if asignacion.id else AsignacionTutorModel()
        m.usuario_id, m.grupo_id, m.periodo_id = asignacion.usuario_id, asignacion.grupo_id, asignacion.periodo_id
        self._s.add(m)
        flush_o_conflicto(self._s)
        asignacion.id = m.id
        return asignacion

    def eliminar(self, asignacion_id: int) -> None:
        m = self._s.get(AsignacionTutorModel, asignacion_id)
        if m is not None:
            self._s.delete(m)
            flush_o_conflicto(self._s)
