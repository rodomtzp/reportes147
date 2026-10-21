from datetime import date

from sqlalchemy import (
    Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, String, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class CarreraModel(Base):
    __tablename__ = "carreras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    clave: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class GrupoModel(Base):
    __tablename__ = "grupos"
    __table_args__ = (
        UniqueConstraint("semestre", "letra", name="uq_grupo_semestre_letra"),
        CheckConstraint("semestre BETWEEN 1 AND 6", name="ck_grupo_semestre"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    carrera_id: Mapped[int] = mapped_column(ForeignKey("carreras.id"), nullable=False, index=True)
    semestre: Mapped[int] = mapped_column(Integer, nullable=False)
    letra: Mapped[str] = mapped_column(String(1), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PeriodoEscolarModel(Base):
    __tablename__ = "periodos_escolares"
    __table_args__ = (
        # Garantiza a nivel de BD que solo haya un periodo vigente.
        Index("uq_periodo_vigente", "vigente", unique=True,
              postgresql_where=text("vigente"), sqlite_where=text("vigente")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AsignacionTutorModel(Base):
    __tablename__ = "asignaciones_tutor"
    __table_args__ = (
        UniqueConstraint("grupo_id", "periodo_id", name="uq_tutor_grupo_periodo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id"), nullable=False)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodos_escolares.id"), nullable=False)
