"""evaluaciones_coloquios

Revision ID: 20260610_011
Revises: 20260610_010
Create Date: 2026-06-10

Migración 011 — C-14 evaluaciones-y-coloquios
Crea las tablas `evaluaciones`, `reservas_evaluacion` y `resultados_evaluacion`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260610_011"
down_revision = "20260610_010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluaciones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="Coloquio"),
        sa.Column("instancia", sa.String(200), nullable=False),
        sa.Column("dias_disponibles", sa.Integer, nullable=False, server_default="1"),
        sa.Column("cupos_por_dia", sa.Integer, nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "tipo IN ('Parcial','TP','Coloquio','Recuperatorio')",
            name="ck_evaluaciones_tipo",
        ),
    )
    op.create_index("ix_evaluaciones_tenant", "evaluaciones", ["tenant_id"])
    op.create_index("ix_evaluaciones_tenant_materia", "evaluaciones", ["tenant_id", "materia_id"])

    op.create_table(
        "reservas_evaluacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluacion_id", UUID(as_uuid=True), sa.ForeignKey("evaluaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("alumno_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fecha_hora", sa.String(50), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Activa','Cancelada')",
            name="ck_reservas_evaluacion_estado",
        ),
    )
    op.create_index("ix_reservas_evaluacion_tenant", "reservas_evaluacion", ["tenant_id"])
    op.create_index("ix_reservas_evaluacion_tenant_evaluacion", "reservas_evaluacion", ["tenant_id", "evaluacion_id"])
    op.create_index("ix_reservas_evaluacion_tenant_alumno", "reservas_evaluacion", ["tenant_id", "alumno_id"])

    op.create_table(
        "resultados_evaluacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluacion_id", UUID(as_uuid=True), sa.ForeignKey("evaluaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("alumno_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nota_final", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_resultados_evaluacion_tenant", "resultados_evaluacion", ["tenant_id"])
    op.create_index("ix_resultados_evaluacion_tenant_evaluacion", "resultados_evaluacion", ["tenant_id", "evaluacion_id"])


def downgrade() -> None:
    op.drop_table("resultados_evaluacion")
    op.drop_table("reservas_evaluacion")
    op.drop_table("evaluaciones")
