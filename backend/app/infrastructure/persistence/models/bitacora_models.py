from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class BitacoraModel(Base):
    __tablename__ = "bitacora_accesos"
    __table_args__ = (Index("ix_bitacora_fecha", "fecha"), Index("ix_bitacora_usuario", "usuario_id"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accion: Mapped[str] = mapped_column(String(24), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)
    estudiante_id: Mapped[Optional[int]] = mapped_column(ForeignKey("estudiantes.id"))
    grupo_id: Mapped[Optional[int]] = mapped_column(Integer)
    carrera_id: Mapped[Optional[int]] = mapped_column(Integer)
    filas: Mapped[Optional[int]] = mapped_column(Integer)
    con_contacto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
