"""estructura académica, catálogos y cambio obligatorio de contraseña

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("debe_cambiar_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "carreras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("clave", sa.String(20), nullable=False, unique=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "grupos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("carrera_id", sa.Integer(), sa.ForeignKey("carreras.id"), nullable=False),
        sa.Column("semestre", sa.Integer(), nullable=False),
        sa.Column("letra", sa.String(1), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("semestre", "letra", name="uq_grupo_semestre_letra"),
        sa.CheckConstraint("semestre BETWEEN 1 AND 6", name="ck_grupo_semestre"),
    )
    op.create_index("ix_grupos_carrera_id", "grupos", ["carrera_id"])
    op.create_table(
        "periodos_escolares",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(30), nullable=False, unique=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "uq_periodo_vigente", "periodos_escolares", ["vigente"], unique=True,
        postgresql_where=sa.text("vigente"),
    )
    op.create_table(
        "asignaciones_tutor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=False),
        sa.Column("periodo_id", sa.Integer(), sa.ForeignKey("periodos_escolares.id"), nullable=False),
        sa.UniqueConstraint("grupo_id", "periodo_id", name="uq_tutor_grupo_periodo"),
    )
    op.create_index("ix_asignaciones_tutor_usuario_id", "asignaciones_tutor", ["usuario_id"])
    op.create_table(
        "tipos_incidencia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("es_otro", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "tipos_sancion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("requiere_dias", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("tipos_sancion")
    op.drop_table("tipos_incidencia")
    op.drop_index("ix_asignaciones_tutor_usuario_id", table_name="asignaciones_tutor")
    op.drop_table("asignaciones_tutor")
    op.drop_index("uq_periodo_vigente", table_name="periodos_escolares")
    op.drop_table("periodos_escolares")
    op.drop_index("ix_grupos_carrera_id", table_name="grupos")
    op.drop_table("grupos")
    op.drop_table("carreras")
    op.drop_column("usuarios", "debe_cambiar_password")
