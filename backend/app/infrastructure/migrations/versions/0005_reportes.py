"""reportes, historial, evidencias y contador de folios

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reportes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("folio", sa.String(20), nullable=False, unique=True),
        sa.Column("incidente_id", sa.String(36), nullable=False),
        sa.Column("estudiante_id", sa.Integer(), sa.ForeignKey("estudiantes.id"), nullable=False),
        sa.Column("inscripcion_id", sa.Integer(), sa.ForeignKey("inscripciones.id"), nullable=False),
        sa.Column("creado_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("tipo_incidencia_id", sa.Integer(), sa.ForeignKey("tipos_incidencia.id"), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("descripcion_otro", sa.String(200)),
        sa.Column("fecha_hora_incidente", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gravedad", sa.String(10), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("cancelado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("motivo_cancelacion", sa.Text()),
        sa.Column("cancelado_por", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("cancelado_en", sa.DateTime(timezone=True)),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reportes_incidente_id", "reportes", ["incidente_id"])
    op.create_index("ix_reportes_creado_por", "reportes", ["creado_por"])
    op.create_index("ix_reportes_estado", "reportes", ["estado"])
    op.create_index("ix_reportes_estudiante_fecha", "reportes", ["estudiante_id", "fecha_hora_incidente"])
    op.create_table(
        "historial_reportes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id"), nullable=False),
        sa.Column("tipo", sa.String(15), nullable=False),
        sa.Column("campo", sa.String(40)),
        sa.Column("valor_anterior", sa.Text()),
        sa.Column("valor_nuevo", sa.Text()),
        sa.Column("comentario", sa.Text()),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_historial_reportes_reporte_id", "historial_reportes", ["reporte_id"])
    op.create_table(
        "adjuntos_reporte",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id"), nullable=False),
        sa.Column("nombre_original", sa.String(120), nullable=False),
        sa.Column("tipo_mime", sa.String(50), nullable=False),
        sa.Column("clave_almacen", sa.String(120), nullable=False),
        sa.Column("tamano", sa.Integer(), nullable=False),
        sa.Column("subido_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("subido_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_adjuntos_reporte_reporte_id", "adjuntos_reporte", ["reporte_id"])
    contadores = op.create_table(
        "folio_contadores",
        sa.Column("anio", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("ultimo", sa.Integer(), nullable=False, server_default="0"),
    )
    # Años precargados: evita que dos reportes simultáneos compitan por crear la fila del año.
    op.bulk_insert(contadores, [{"anio": a, "ultimo": 0} for a in range(2026, 2041)])


def downgrade() -> None:
    op.drop_table("folio_contadores")
    op.drop_index("ix_adjuntos_reporte_reporte_id", table_name="adjuntos_reporte")
    op.drop_table("adjuntos_reporte")
    op.drop_index("ix_historial_reportes_reporte_id", table_name="historial_reportes")
    op.drop_table("historial_reportes")
    op.drop_index("ix_reportes_estudiante_fecha", table_name="reportes")
    op.drop_index("ix_reportes_estado", table_name="reportes")
    op.drop_index("ix_reportes_creado_por", table_name="reportes")
    op.drop_index("ix_reportes_incidente_id", table_name="reportes")
    op.drop_table("reportes")
