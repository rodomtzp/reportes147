"""intentos de llamada y mensajes de WhatsApp

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intentos_llamada",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id"), nullable=False),
        sa.Column("tutor_legal_id", sa.Integer(), sa.ForeignKey("tutores_legales.id"), nullable=False),
        sa.Column("estado", sa.String(12), nullable=False),
        sa.Column("realizado_por", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("fecha_hora", sa.DateTime(timezone=True)),
        sa.Column("atendio_nombre", sa.String(120)),
        sa.Column("observaciones", sa.Text()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_intentos_llamada_reporte_id", "intentos_llamada", ["reporte_id"])
    op.create_index("ix_intentos_llamada_tutor_legal_id", "intentos_llamada", ["tutor_legal_id"])
    op.create_table(
        "mensajes_whatsapp",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id"), nullable=False),
        sa.Column("tutor_legal_id", sa.Integer(), sa.ForeignKey("tutores_legales.id"), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("generado_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("generado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enviado_en", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_mensajes_whatsapp_reporte_id", "mensajes_whatsapp", ["reporte_id"])
    op.create_index("ix_mensajes_whatsapp_tutor_legal_id", "mensajes_whatsapp", ["tutor_legal_id"])
    # Reportes creados antes de esta fase: su llamada pendiente, al padre o tutor principal.
    op.execute("""
        INSERT INTO intentos_llamada (reporte_id, tutor_legal_id, estado, creado_en)
        SELECT r.id,
               (SELECT t.id FROM tutores_legales t WHERE t.estudiante_id = r.estudiante_id
                ORDER BY t.es_principal DESC, t.id LIMIT 1),
               'PENDIENTE', r.creado_en
        FROM reportes r
        WHERE EXISTS (SELECT 1 FROM tutores_legales t WHERE t.estudiante_id = r.estudiante_id)
    """)


def downgrade() -> None:
    op.drop_index("ix_mensajes_whatsapp_tutor_legal_id", table_name="mensajes_whatsapp")
    op.drop_index("ix_mensajes_whatsapp_reporte_id", table_name="mensajes_whatsapp")
    op.drop_table("mensajes_whatsapp")
    op.drop_index("ix_intentos_llamada_tutor_legal_id", table_name="intentos_llamada")
    op.drop_index("ix_intentos_llamada_reporte_id", table_name="intentos_llamada")
    op.drop_table("intentos_llamada")
