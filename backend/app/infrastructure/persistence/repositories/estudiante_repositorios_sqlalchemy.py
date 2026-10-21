from typing import Dict, Iterable, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.application.ports.repositorios import (
    EstudianteRepositorio, InscripcionRepositorio, TutorLegalRepositorio,
)
from app.domain.entities.estudiante import Estudiante
from app.domain.entities.inscripcion import Inscripcion
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
from app.infrastructure.persistence.models import (
    EstudianteModel, GrupoModel, InscripcionModel, PeriodoEscolarModel, TutorLegalModel,
)
from app.infrastructure.persistence.utils import flush_o_conflicto

_CAMPOS = (
    "numero_control", "primer_apellido", "segundo_apellido", "nombres", "telefono", "correo",
    "calle", "numero", "colonia", "ciudad", "generacion",
)


def _estudiante(m: EstudianteModel) -> Estudiante:
    return Estudiante(id=m.id, estatus=EstatusEstudiante(m.estatus), **{c: getattr(m, c) for c in _CAMPOS})


def _patron(token: str) -> str:
    escapado = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def _filtrar_texto(q, texto: Optional[str]):
    """Cada palabra debe aparecer en número de control, apellidos o nombres."""
    for token in (texto or "").split():
        p = _patron(token)
        q = q.where(or_(*(getattr(EstudianteModel, c).ilike(p, escape="\\") for c in (
            "numero_control", "primer_apellido", "segundo_apellido", "nombres"))))
    return q


_ORDEN = (EstudianteModel.primer_apellido, EstudianteModel.segundo_apellido, EstudianteModel.nombres)


class EstudianteRepositorioSQLAlchemy(EstudianteRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, estudiante_id: int) -> Optional[Estudiante]:
        m = self._s.get(EstudianteModel, estudiante_id)
        return _estudiante(m) if m else None

    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Estudiante]:
        ids = list(ids)
        if not ids:
            return {}
        filas = self._s.scalars(select(EstudianteModel).where(EstudianteModel.id.in_(ids))).all()
        return {m.id: _estudiante(m) for m in filas}

    def obtener_por_numero_control(self, numero_control: str) -> Optional[Estudiante]:
        m = self._s.scalar(
            select(EstudianteModel).where(EstudianteModel.numero_control == numero_control.strip().upper())
        )
        return _estudiante(m) if m else None

    def listar(self, texto=None, estatus=None, grupo_ids=None, carrera_id=None, periodo_id=None,
               limite=200, offset=0) -> List[Estudiante]:
        q = _filtrar_texto(select(EstudianteModel), texto)
        if estatus is not None:
            q = q.where(EstudianteModel.estatus == EstatusEstudiante(estatus).value)
        if grupo_ids is not None or carrera_id is not None:
            q = q.join(InscripcionModel, InscripcionModel.estudiante_id == EstudianteModel.id).where(
                InscripcionModel.periodo_id == periodo_id
            )
            if grupo_ids is not None:
                q = q.where(InscripcionModel.grupo_id.in_(grupo_ids))
            if carrera_id is not None:
                q = q.join(GrupoModel, GrupoModel.id == InscripcionModel.grupo_id).where(
                    GrupoModel.carrera_id == carrera_id
                )
        q = q.order_by(*_ORDEN).limit(limite).offset(offset)
        return [_estudiante(m) for m in self._s.scalars(q).all()]

    def buscar_activos(self, texto: str, limite: int = 15) -> List[Estudiante]:
        q = _filtrar_texto(select(EstudianteModel), texto).where(
            EstudianteModel.estatus == EstatusEstudiante.ACTIVO.value
        ).order_by(*_ORDEN).limit(limite)
        return [_estudiante(m) for m in self._s.scalars(q).all()]

    def guardar(self, estudiante: Estudiante) -> Estudiante:
        m = self._s.get(EstudianteModel, estudiante.id) if estudiante.id else EstudianteModel()
        for c in _CAMPOS:
            setattr(m, c, getattr(estudiante, c))
        m.estatus = EstatusEstudiante(estudiante.estatus).value
        self._s.add(m)
        flush_o_conflicto(self._s)
        estudiante.id = m.id
        return estudiante


def _tutor(m: TutorLegalModel) -> TutorLegal:
    return TutorLegal(
        id=m.id, estudiante_id=m.estudiante_id, nombre=m.nombre, parentesco=m.parentesco,
        telefono=m.telefono, correo=m.correo, es_principal=m.es_principal,
    )


class TutorLegalRepositorioSQLAlchemy(TutorLegalRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, tutor_id: int) -> Optional[TutorLegal]:
        m = self._s.get(TutorLegalModel, tutor_id)
        return _tutor(m) if m else None

    def listar_por_estudiante(self, estudiante_id: int) -> List[TutorLegal]:
        q = select(TutorLegalModel).where(TutorLegalModel.estudiante_id == estudiante_id).order_by(
            TutorLegalModel.es_principal.desc(), TutorLegalModel.id
        )
        return [_tutor(m) for m in self._s.scalars(q).all()]

    def guardar(self, tutor: TutorLegal) -> TutorLegal:
        m = self._s.get(TutorLegalModel, tutor.id) if tutor.id else TutorLegalModel()
        m.estudiante_id, m.nombre, m.parentesco = tutor.estudiante_id, tutor.nombre, tutor.parentesco
        m.telefono, m.correo, m.es_principal = tutor.telefono, tutor.correo, tutor.es_principal
        self._s.add(m)
        flush_o_conflicto(self._s)
        tutor.id = m.id
        return tutor

    def eliminar(self, tutor_id: int) -> None:
        m = self._s.get(TutorLegalModel, tutor_id)
        if m is not None:
            self._s.delete(m)
            flush_o_conflicto(self._s)


def _inscripcion(m: InscripcionModel) -> Inscripcion:
    return Inscripcion(id=m.id, estudiante_id=m.estudiante_id, grupo_id=m.grupo_id, periodo_id=m.periodo_id)


class InscripcionRepositorioSQLAlchemy(InscripcionRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener(self, estudiante_id: int, periodo_id: int) -> Optional[Inscripcion]:
        m = self._s.scalar(select(InscripcionModel).where(
            InscripcionModel.estudiante_id == estudiante_id, InscripcionModel.periodo_id == periodo_id))
        return _inscripcion(m) if m else None

    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Inscripcion]:
        ids = list(ids)
        if not ids:
            return {}
        filas = self._s.scalars(select(InscripcionModel).where(InscripcionModel.id.in_(ids))).all()
        return {m.id: _inscripcion(m) for m in filas}

    def obtener_de_estudiantes(self, ids: Iterable[int], periodo_id: int) -> Dict[int, Inscripcion]:
        ids = list(ids)
        if not ids:
            return {}
        q = select(InscripcionModel).where(
            InscripcionModel.estudiante_id.in_(ids), InscripcionModel.periodo_id == periodo_id)
        return {m.estudiante_id: _inscripcion(m) for m in self._s.scalars(q).all()}

    def listar_por_estudiante(self, estudiante_id: int) -> List[Inscripcion]:
        q = (select(InscripcionModel)
             .join(PeriodoEscolarModel, PeriodoEscolarModel.id == InscripcionModel.periodo_id)
             .where(InscripcionModel.estudiante_id == estudiante_id)
             .order_by(PeriodoEscolarModel.fecha_inicio))
        return [_inscripcion(m) for m in self._s.scalars(q).all()]

    def listar_por_periodo(self, periodo_id: int) -> List[Inscripcion]:
        q = select(InscripcionModel).where(InscripcionModel.periodo_id == periodo_id).order_by(InscripcionModel.id)
        return [_inscripcion(m) for m in self._s.scalars(q).all()]

    def guardar(self, inscripcion: Inscripcion) -> Inscripcion:
        m = self._s.get(InscripcionModel, inscripcion.id) if inscripcion.id else InscripcionModel()
        m.estudiante_id, m.grupo_id, m.periodo_id = inscripcion.estudiante_id, inscripcion.grupo_id, inscripcion.periodo_id
        self._s.add(m)
        flush_o_conflicto(self._s)
        inscripcion.id = m.id
        return inscripcion
