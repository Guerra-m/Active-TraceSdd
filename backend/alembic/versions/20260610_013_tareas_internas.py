"""tareas_internas

Revision ID: 20260610_013
Revises: 20260610_012
Create Date: 2026-06-10

Migración 013 — C-16 tareas-internas
Crea las tablas `tareas` y `comentarios_tarea`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260610_013"
down_revision = "20260610_012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tareas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asignado_a", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asignado_por", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("contexto_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Pendiente','En progreso','Resuelta','Cancelada')",
            name="ck_tareas_estado",
        ),
    )
    op.create_index("ix_tareas_tenant", "tareas", ["tenant_id"])
    op.create_index("ix_tareas_tenant_asignado_a", "tareas", ["tenant_id", "asignado_a"])
    op.create_index("ix_tareas_tenant_estado", "tareas", ["tenant_id", "estado"])

    op.create_table(
        "comentarios_tarea",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tarea_id", UUID(as_uuid=True), sa.ForeignKey("tareas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("autor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("texto", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_comentarios_tarea_tenant", "comentarios_tarea", ["tenant_id"])
    op.create_index("ix_comentarios_tarea_tenant_tarea", "comentarios_tarea", ["tenant_id", "tarea_id"])


def downgrade() -> None:
    op.drop_table("comentarios_tarea")
    op.drop_table("tareas")
