from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sesion_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    roles: Mapped[List["UsuarioRolModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class UsuarioRolModel(Base):
    __tablename__ = "usuario_roles"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    rol: Mapped[str] = mapped_column(String(30), primary_key=True)
