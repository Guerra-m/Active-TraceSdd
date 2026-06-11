"""encuentros_guardias

Revision ID: 20260610_010
Revises: 20260610_009
Create Date: 2026-06-10

Migración 010 — C-13 encuentros-y-guardias
Crea las tablas `slot_encuentros`, `instancias_encuentro` y `guardias`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260610_010"
down_revision = "20260610_009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "slot_encuentros",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asignacion_id", UUID(as_uuid=True), sa.ForeignKey("asignaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("dia_semana", sa.String(15), nullable=True),
        sa.Column("fecha_inicio", sa.Date, nullable=True),
        sa.Column("cant_semanas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fecha_unica", sa.Date, nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date, nullable=True),
        sa.Column("vig_hasta", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "dia_semana IN ('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo')",
            name="ck_slot_encuentros_dia_semana",
        ),
    )
    op.create_index("ix_slot_encuentros_tenant", "slot_encuentros", ["tenant_id"])
    op.create_index("ix_slot_encuentros_tenant_materia", "slot_encuentros", ["tenant_id", "materia_id"])

    op.create_table(
        "instancias_encuentro",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("slot_id", UUID(as_uuid=True), sa.ForeignKey("slot_encuentros.id", ondelete="SET NULL"), nullable=True),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Programado"),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Programado','Realizado','Cancelado')",
            name="ck_instancias_encuentro_estado",
        ),
    )
    op.create_index("ix_instancias_encuentro_tenant", "instancias_encuentro", ["tenant_id"])
    op.create_index("ix_instancias_encuentro_tenant_materia", "instancias_encuentro", ["tenant_id", "materia_id"])
    op.create_index("ix_instancias_encuentro_tenant_fecha", "instancias_encuentro", ["tenant_id", "fecha"])

    op.create_table(
        "guardias",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asignacion_id", UUID(as_uuid=True), sa.ForeignKey("asignaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("carrera_id", UUID(as_uuid=True), sa.ForeignKey("carreras.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dia", sa.String(15), nullable=False),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("comentarios", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "dia IN ('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo')",
            name="ck_guardias_dia",
        ),
        sa.CheckConstraint(
            "estado IN ('Pendiente','Realizada','Cancelada')",
            name="ck_guardias_estado",
        ),
    )
    op.create_index("ix_guardias_tenant", "guardias", ["tenant_id"])
    op.create_index("ix_guardias_tenant_asignacion", "guardias", ["tenant_id", "asignacion_id"])


def downgrade() -> None:
    op.drop_table("guardias")
    op.drop_table("instancias_encuentro")
    op.drop_table("slot_encuentros")
