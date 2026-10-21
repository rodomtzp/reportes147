"""ciclos de acumulación, sanciones y bandeja de alertas

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ciclos_acumulacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("abierto", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("estudiante_id", "numero", name="uq_ciclo_estudiante_numero"),
    )
    op.create_index("uq_ciclo_abierto_por_estudiante", "ciclos_acumulacion", ["estudiante_id"], unique=True,
                    postgresql_where=sa.text("abierto"))

    op.add_column("reportes", sa.Column("ciclo_id", sa.Integer(), sa.ForeignKey("ciclos_acumulacion.id")))
    op.add_column("reportes", sa.Column("cuenta_acumulacion", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_reportes_ciclo_id", "reportes", ["ciclo_id"])
    # Reportes anteriores a esta fase: todos pertenecen al primer ciclo (abierto) de su estudiante.
    op.execute("""
        INSERT INTO ciclos_acumulacion (estudiante_id, numero, abierto, fecha_inicio)
        SELECT estudiante_id, 1, TRUE, MIN(creado_en) FROM reportes GROUP BY estudiante_id
    """)
    op.execute("""
        UPDATE reportes SET ciclo_id = (
            SELECT c.id FROM ciclos_acumulacion c WHERE c.estudiante_id = reportes.estudiante_id AND c.numero = 1)
    """)

    op.create_table(
        "sanciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo_sancion_id", sa.Integer(), sa.ForeignKey("tipos_sancion.id"), nullable=False),
        sa.Column("origen", sa.String(12), nullable=False),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id"), nullable=False),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id")),
        sa.Column("ciclo_id", sa.Integer(), sa.ForeignKey("ciclos_acumulacion.id")),
        sa.Column("dias", sa.Integer()),
        sa.Column("observaciones", sa.Text()),
        sa.Column("aplicada_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("aplicada_en", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("reporte_id", name="uq_sancion_reporte"),
        sa.UniqueConstraint("ciclo_id", name="uq_sancion_ciclo"),
        sa.CheckConstraint(
            "(origen = 'DIRECTA' AND reporte_id IS NOT NULL AND ciclo_id IS NULL) OR "
            "(origen = 'ACUMULACION' AND ciclo_id IS NOT NULL AND reporte_id IS NULL)", name="ck_sancion_origen"),
    )
    op.create_index("ix_sanciones_estudiante_id", "sanciones", ["estudiante_id"])

    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("rol_destino", sa.String(20), nullable=False),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id")),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id")),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correo_enviado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("correo_error", sa.String(300)),
        sa.Column("atendida_por", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("atendida_en", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notificaciones_rol_atendida", "notificaciones", ["rol_destino", "atendida_en"])


def downgrade() -> None:
    op.drop_index("ix_notificaciones_rol_atendida", table_name="notificaciones")
    op.drop_table("notificaciones")
    op.drop_index("ix_sanciones_estudiante_id", table_name="sanciones")
    op.drop_table("sanciones")
    op.drop_index("ix_reportes_ciclo_id", table_name="reportes")
    op.drop_column("reportes", "cuenta_acumulacion")
    op.drop_column("reportes", "ciclo_id")
    op.drop_index("uq_ciclo_abierto_por_estudiante", table_name="ciclos_acumulacion")
    op.drop_table("ciclos_acumulacion")
