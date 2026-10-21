from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class CicloAcumulacionModel(Base):
    __tablename__ = "ciclos_acumulacion"
    __table_args__ = (
        UniqueConstraint("estudiante_id", "numero", name="uq_ciclo_estudiante_numero"),
        # A lo más un ciclo abierto por estudiante.
        Index("uq_ciclo_abierto_por_estudiante", "estudiante_id", unique=True,
              postgresql_where=text("abierto"), sqlite_where=text("abierto")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    abierto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class SancionModel(Base):
    __tablename__ = "sanciones"
    __table_args__ = (
        UniqueConstraint("reporte_id", name="uq_sancion_reporte"),   # una sanción directa por reporte
        UniqueConstraint("ciclo_id", name="uq_sancion_ciclo"),       # una sanción por acumulación por ciclo
        CheckConstraint(
            "(origen = 'DIRECTA' AND reporte_id IS NOT NULL AND ciclo_id IS NULL) OR "
            "(origen = 'ACUMULACION' AND ciclo_id IS NOT NULL AND reporte_id IS NULL)",
            name="ck_sancion_origen"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_sancion_id: Mapped[int] = mapped_column(ForeignKey("tipos_sancion.id"), nullable=False)
    origen: Mapped[str] = mapped_column(String(12), nullable=False)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"), nullable=False, index=True)
    reporte_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reportes.id"))
    ciclo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ciclos_acumulacion.id"))
    dias: Mapped[Optional[int]] = mapped_column(Integer)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    aplicada_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    aplicada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotificacionModel(Base):
    __tablename__ = "notificaciones"
    __table_args__ = (Index("ix_notificaciones_rol_atendida", "rol_destino", "atendida_en"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    rol_destino: Mapped[str] = mapped_column(String(20), nullable=False)
    reporte_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reportes.id"))
    estudiante_id: Mapped[Optional[int]] = mapped_column(ForeignKey("estudiantes.id"))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correo_enviado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correo_error: Mapped[Optional[str]] = mapped_column(String(300))
    atendida_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    atendida_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
