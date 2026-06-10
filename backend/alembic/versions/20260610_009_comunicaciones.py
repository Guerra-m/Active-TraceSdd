"""comunicaciones

Revision ID: 20260610_009
Revises: 20260610_008
Create Date: 2026-06-10

Migración 009 — C-12 comunicaciones-cola-worker
Crea las tablas `lotes_comunicacion` y `comunicaciones`.

lotes_comunicacion: cabecera de un envío (template + estado del lote).
                   Permite aprobar / cancelar el lote completo atómicamente.

comunicaciones: mensaje individual (destinatario cifrado, asunto/cuerpo renderizados,
                máquina de estados RN-15).

upgrade  : CREATE TABLE lotes_comunicacion → CREATE TABLE comunicaciones
downgrade: DROP TABLE comunicaciones → DROP TABLE lotes_comunicacion
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_009"
down_revision = "20260610_008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. lotes_comunicacion
    # ------------------------------------------------------------------
    op.create_table(
        "lotes_comunicacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "enviado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("asunto_template", sa.Text, nullable=False),
        sa.Column("cuerpo_template", sa.Text, nullable=False),
        # Estado del lote: Pendiente|PendienteAprobacion|Aprobado|Despachando|Completado|Cancelado
        sa.Column(
            "estado",
            sa.String(30),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column(
            "requiere_aprobacion",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "aprobado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_mensajes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enviados", sa.Integer, nullable=False, server_default="0"),
        sa.Column("errores", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Pendiente','PendienteAprobacion','Aprobado','Despachando','Completado','Cancelado')",
            name="ck_lotes_comunicacion_estado",
        ),
    )
    op.create_index("ix_lotes_comunicacion_tenant", "lotes_comunicacion", ["tenant_id"])
    op.create_index(
        "ix_lotes_comunicacion_tenant_estado",
        "lotes_comunicacion",
        ["tenant_id", "estado"],
    )

    # ------------------------------------------------------------------
    # 2. comunicaciones
    # ------------------------------------------------------------------
    op.create_table(
        "comunicaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "lote_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lotes_comunicacion.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enviado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "entrada_padron_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entrada_padron.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # PII cifrada AES-256-GCM — nunca texto plano
        sa.Column("destinatario", sa.Text, nullable=False),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text, nullable=False),
        # Estado: Pendiente|Enviando|Enviado|Error|Cancelado (RN-15)
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Pendiente','Enviando','Enviado','Error','Cancelado')",
            name="ck_comunicaciones_estado",
        ),
    )
    op.create_index("ix_comunicaciones_tenant_lote", "comunicaciones", ["tenant_id", "lote_id"])
    op.create_index(
        "ix_comunicaciones_tenant_estado", "comunicaciones", ["tenant_id", "estado"]
    )
    op.create_index(
        "ix_comunicaciones_tenant_entrada_padron",
        "comunicaciones",
        ["tenant_id", "entrada_padron_id"],
    )


def downgrade() -> None:
    op.drop_table("comunicaciones")
    op.drop_table("lotes_comunicacion")
