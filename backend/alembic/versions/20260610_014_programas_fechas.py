"""programas_fechas_academicas

Revision ID: 20260610_014
Revises: 20260610_013
Create Date: 2026-06-10

Migración 014 — C-17 programas-y-fechas-academicas
Crea las tablas `fechas_academicas` y `programas_materia`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260610_014"
down_revision = "20260610_013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fechas_academicas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("numero", sa.Integer, nullable=False, server_default="1"),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "tipo IN ('Parcial','TP','Coloquio','Recuperatorio')",
            name="ck_fechas_academicas_tipo",
        ),
    )
    op.create_index("ix_fechas_academicas_tenant", "fechas_academicas", ["tenant_id"])
    op.create_index("ix_fechas_academicas_tenant_materia", "fechas_academicas", ["tenant_id", "materia_id"])
    op.create_index("ix_fechas_academicas_tenant_periodo", "fechas_academicas", ["tenant_id", "periodo"])

    op.create_table(
        "programas_materia",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("carrera_id", UUID(as_uuid=True), sa.ForeignKey("carreras.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("referencia_archivo", sa.Text, nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_programas_materia_tenant", "programas_materia", ["tenant_id"])
    op.create_index("ix_programas_materia_tenant_materia", "programas_materia", ["tenant_id", "materia_id"])


def downgrade() -> None:
    op.drop_table("programas_materia")
    op.drop_table("fechas_academicas")
