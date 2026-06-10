"""calificaciones

Revision ID: 20260610_008
Revises: 20260610_007
Create Date: 2026-06-10

Migración 008 — C-10 calificaciones-y-umbral
Crea las tablas `umbral_materia` y `calificaciones`.

umbral_materia: configuración de aprobación por asignación × materia.
               Default 60%; valores textuales aprobatorios en JSONB.

calificaciones: nota numérica o textual de un alumno en una actividad evaluable.
                campo `aprobado` calculado al importar con el umbral vigente.
                `entrada_padron_id` nullable: permite importar sin padrón activo.

upgrade  : CREATE TABLE umbral_materia + CREATE TABLE calificaciones
downgrade: DROP TABLE calificaciones → DROP TABLE umbral_materia
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_008"
down_revision = "20260610_007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla umbral_materia
    # ------------------------------------------------------------------
    op.create_table(
        "umbral_materia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asignaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("umbral_pct", sa.SmallInteger, nullable=False, server_default="60"),
        sa.Column(
            "valores_aprobatorios",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text('\'["Satisfactorio","Supera lo esperado"]\'::jsonb'),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_umbral_materia_asignacion_materia",
        "umbral_materia",
        ["tenant_id", "asignacion_id", "materia_id"],
    )
    op.create_index("ix_umbral_materia_tenant", "umbral_materia", ["tenant_id"])
    op.create_index(
        "ix_umbral_materia_asignacion",
        "umbral_materia", ["tenant_id", "asignacion_id", "materia_id"],
    )

    # ------------------------------------------------------------------
    # 2. Tabla calificaciones
    # ------------------------------------------------------------------
    op.create_table(
        "calificaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asignaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "entrada_padron_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entrada_padron.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actividad", sa.String(500), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(6, 2), nullable=True),
        sa.Column("nota_textual", sa.String(200), nullable=True),
        sa.Column("aprobado", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("origen", sa.String(20), nullable=False, server_default="Importado"),
        sa.Column("importado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_calificaciones_tenant_asignacion_materia",
        "calificaciones", ["tenant_id", "asignacion_id", "materia_id"],
    )
    op.create_index(
        "ix_calificaciones_tenant_materia",
        "calificaciones", ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_calificaciones_tenant_entrada_padron",
        "calificaciones", ["tenant_id", "entrada_padron_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_calificaciones_tenant_entrada_padron", table_name="calificaciones")
    op.drop_index("ix_calificaciones_tenant_materia", table_name="calificaciones")
    op.drop_index("ix_calificaciones_tenant_asignacion_materia", table_name="calificaciones")
    op.drop_table("calificaciones")

    op.drop_index("ix_umbral_materia_asignacion", table_name="umbral_materia")
    op.drop_index("ix_umbral_materia_tenant", table_name="umbral_materia")
    op.drop_constraint("uq_umbral_materia_asignacion_materia", "umbral_materia")
    op.drop_table("umbral_materia")
