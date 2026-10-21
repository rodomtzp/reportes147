"""catálogos iniciales de incidencias y sanciones

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

INCIDENCIAS = [
    "Indisciplina en aula",
    "Faltas de respeto",
    "Uso indebido de uniforme",
    "Asistencia",
    "Pelea",
    "Vandalizar",
]
SANCIONES = [
    ("Suspensión de N días", True),
    ("Carta compromiso", False),
    ("Servicio comunitario interno", False),
]


def upgrade() -> None:
    incidencias = sa.table(
        "tipos_incidencia",
        sa.column("nombre", sa.String), sa.column("activo", sa.Boolean), sa.column("es_otro", sa.Boolean),
    )
    op.bulk_insert(
        incidencias,
        [{"nombre": n, "activo": True, "es_otro": False} for n in INCIDENCIAS]
        + [{"nombre": "Otro", "activo": True, "es_otro": True}],
    )
    sanciones = sa.table(
        "tipos_sancion",
        sa.column("nombre", sa.String), sa.column("requiere_dias", sa.Boolean), sa.column("activo", sa.Boolean),
    )
    op.bulk_insert(
        sanciones,
        [{"nombre": n, "requiere_dias": d, "activo": True} for n, d in SANCIONES],
    )


def downgrade() -> None:
    nombres_i = ", ".join(f"'{n}'" for n in INCIDENCIAS + ["Otro"])
    nombres_s = ", ".join(f"'{n}'" for n, _ in SANCIONES)
    op.execute(f"DELETE FROM tipos_incidencia WHERE nombre IN ({nombres_i})")
    op.execute(f"DELETE FROM tipos_sancion WHERE nombre IN ({nombres_s})")
