"""avisos_acknowledgment

Revision ID: 20260610_012
Revises: 20260610_011
Create Date: 2026-06-10

Migración 012 — C-15 avisos-y-acknowledgment
Crea las tablas `avisos` y `acknowledgments_aviso`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260610_012"
down_revision = "20260610_011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "avisos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("alcance", sa.String(20), nullable=False, server_default="Global"),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rol_destino", sa.String(30), nullable=True),
        sa.Column("severidad", sa.String(15), nullable=False, server_default="Info"),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("cuerpo", sa.Text, nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("orden", sa.Integer, nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("requiere_ack", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "alcance IN ('Global','PorMateria','PorCohorte','PorRol')",
            name="ck_avisos_alcance",
        ),
        sa.CheckConstraint(
            "severidad IN ('Info','Advertencia','Crítico')",
            name="ck_avisos_severidad",
        ),
    )
    op.create_index("ix_avisos_tenant", "avisos", ["tenant_id"])
    op.create_index("ix_avisos_tenant_activo", "avisos", ["tenant_id", "activo"])

    op.create_table(
        "acknowledgments_aviso",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aviso_id", UUID(as_uuid=True), sa.ForeignKey("avisos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_acks_aviso_tenant", "acknowledgments_aviso", ["tenant_id"])
    op.create_index("ix_acks_aviso_tenant_aviso", "acknowledgments_aviso", ["tenant_id", "aviso_id"])
    op.create_index("ix_acks_aviso_tenant_usuario", "acknowledgments_aviso", ["tenant_id", "usuario_id"])


def downgrade() -> None:
    op.drop_table("acknowledgments_aviso")
    op.drop_table("avisos")
