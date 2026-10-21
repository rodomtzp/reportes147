from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class EstudianteModel(Base):
    __tablename__ = "estudiantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_control: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    primer_apellido: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    segundo_apellido: Mapped[Optional[str]] = mapped_column(String(80))
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(10))
    correo: Mapped[Optional[str]] = mapped_column(String(254))
    calle: Mapped[Optional[str]] = mapped_column(String(120))
    numero: Mapped[Optional[str]] = mapped_column(String(20))
    colonia: Mapped[Optional[str]] = mapped_column(String(120))
    ciudad: Mapped[Optional[str]] = mapped_column(String(120))
    generacion: Mapped[str] = mapped_column(String(20), nullable=False)
    estatus: Mapped[str] = mapped_column(String(12), nullable=False, default="ACTIVO", index=True)


class TutorLegalModel(Base):
    __tablename__ = "tutores_legales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    parentesco: Mapped[Optional[str]] = mapped_column(String(50))
    telefono: Mapped[str] = mapped_column(String(10), nullable=False)
    correo: Mapped[Optional[str]] = mapped_column(String(254))
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class InscripcionModel(Base):
    __tablename__ = "inscripciones"
    __table_args__ = (
        UniqueConstraint("estudiante_id", "periodo_id", name="uq_inscripcion_estudiante_periodo"),
        Index("ix_inscripciones_periodo_grupo", "periodo_id", "grupo_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"), nullable=False)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id"), nullable=False)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodos_escolares.id"), nullable=False)
