"""estudiantes, padres o tutores legales e inscripciones

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estudiantes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero_control", sa.String(20), nullable=False, unique=True),
        sa.Column("primer_apellido", sa.String(80), nullable=False),
        sa.Column("segundo_apellido", sa.String(80)),
        sa.Column("nombres", sa.String(120), nullable=False),
        sa.Column("telefono", sa.String(10)),
        sa.Column("correo", sa.String(254)),
        sa.Column("calle", sa.String(120)),
        sa.Column("numero", sa.String(20)),
        sa.Column("colonia", sa.String(120)),
        sa.Column("ciudad", sa.String(120)),
        sa.Column("generacion", sa.String(20), nullable=False),
        sa.Column("estatus", sa.String(12), nullable=False, server_default="ACTIVO"),
    )
    op.create_index("ix_estudiantes_primer_apellido", "estudiantes", ["primer_apellido"])
    op.create_index("ix_estudiantes_estatus", "estudiantes", ["estatus"])
    op.create_table(
        "tutores_legales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id"), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("parentesco", sa.String(50)),
        sa.Column("telefono", sa.String(10), nullable=False),
        sa.Column("correo", sa.String(254)),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_tutores_legales_estudiante_id", "tutores_legales", ["estudiante_id"])
    op.create_table(
        "inscripciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id"), nullable=False),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("grupos.id"), nullable=False),
        sa.Column("periodo_id", sa.Integer(), sa.ForeignKey("periodos_escolares.id"), nullable=False),
        sa.UniqueConstraint("estudiante_id", "periodo_id", name="uq_inscripcion_estudiante_periodo"),
    )
    op.create_index("ix_inscripciones_periodo_grupo", "inscripciones", ["periodo_id", "grupo_id"])


def downgrade() -> None:
    op.drop_index("ix_inscripciones_periodo_grupo", table_name="inscripciones")
    op.drop_table("inscripciones")
    op.drop_index("ix_tutores_legales_estudiante_id", table_name="tutores_legales")
    op.drop_table("tutores_legales")
    op.drop_index("ix_estudiantes_estatus", table_name="estudiantes")
    op.drop_index("ix_estudiantes_primer_apellido", table_name="estudiantes")
    op.drop_table("estudiantes")
