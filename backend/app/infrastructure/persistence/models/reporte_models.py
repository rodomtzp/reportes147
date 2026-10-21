from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class ReporteModel(Base):
    __tablename__ = "reportes"
    __table_args__ = (Index("ix_reportes_estudiante_fecha", "estudiante_id", "fecha_hora_incidente"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    incidente_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"), nullable=False)
    inscripcion_id: Mapped[int] = mapped_column(ForeignKey("inscripciones.id"), nullable=False)
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo_incidencia_id: Mapped[int] = mapped_column(ForeignKey("tipos_incidencia.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion_otro: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_hora_incidente: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gravedad: Mapped[str] = mapped_column(String(10), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    cancelado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    motivo_cancelacion: Mapped[Optional[str]] = mapped_column(Text)
    cancelado_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    cancelado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ciclo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ciclos_acumulacion.id"), index=True)
    cuenta_acumulacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class HistorialReporteModel(Base):
    __tablename__ = "historial_reportes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(15), nullable=False)
    campo: Mapped[Optional[str]] = mapped_column(String(40))
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text)
    valor_nuevo: Mapped[Optional[str]] = mapped_column(Text)
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AdjuntoModel(Base):
    __tablename__ = "adjuntos_reporte"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id"), nullable=False, index=True)
    nombre_original: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_mime: Mapped[str] = mapped_column(String(50), nullable=False)
    clave_almacen: Mapped[str] = mapped_column(String(120), nullable=False)
    tamano: Mapped[int] = mapped_column(Integer, nullable=False)
    subido_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    subido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FolioContadorModel(Base):
    __tablename__ = "folio_contadores"

    anio: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ultimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
