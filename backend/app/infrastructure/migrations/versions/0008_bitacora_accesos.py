"""bitácora de accesos a datos de contacto y exportaciones

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bitacora_accesos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("accion", sa.String(24), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=False),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id")),
        sa.Column("grupo_id", sa.Integer()),
        sa.Column("carrera_id", sa.Integer()),
        sa.Column("filas", sa.Integer()),
        sa.Column("con_contacto", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_bitacora_fecha", "bitacora_accesos", ["fecha"])
    op.create_index("ix_bitacora_usuario", "bitacora_accesos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_bitacora_usuario", table_name="bitacora_accesos")
    op.drop_index("ix_bitacora_fecha", table_name="bitacora_accesos")
    op.drop_table("bitacora_accesos")
