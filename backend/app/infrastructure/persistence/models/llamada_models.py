from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class IntentoLlamadaModel(Base):
    __tablename__ = "intentos_llamada"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id"), nullable=False, index=True)
    tutor_legal_id: Mapped[int] = mapped_column(ForeignKey("tutores_legales.id"), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(12), nullable=False)
    realizado_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    fecha_hora: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    atendio_nombre: Mapped[Optional[str]] = mapped_column(String(120))
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MensajeWhatsAppModel(Base):
    __tablename__ = "mensajes_whatsapp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporte_id: Mapped[int] = mapped_column(ForeignKey("reportes.id"), nullable=False, index=True)
    tutor_legal_id: Mapped[int] = mapped_column(ForeignKey("tutores_legales.id"), nullable=False, index=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    generado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    generado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enviado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
