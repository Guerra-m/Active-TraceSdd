"""audit_log

Revision ID: 20260610_004
Revises: 20260610_003
Create Date: 2026-06-10

Migración 004 — C-05 audit-log
Crea la tabla audit_log (E-AUD) con garantía de inmutabilidad a nivel DB:
  - Tabla con campos según knowledge-base/04_modelo_de_datos.md §E-AUD
  - Índices en (tenant_id, fecha_hora DESC) y (tenant_id, actor_id)
  - Trigger BEFORE UPDATE OR DELETE que rechaza toda modificación (append-only)

materia_id se almacena como UUID sin FK (la FK se añade en C-06 cuando
se cree la tabla 'materias').

upgrade  : crea tabla audit_log + índices + función trigger + trigger
downgrade: elimina trigger + función + tabla
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_004"
down_revision = "20260610_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "impersonado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        # materia_id sin FK — se añade en C-06 (migration 005)
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("accion", sa.String(200), nullable=False),
        sa.Column("detalle", postgresql.JSONB, nullable=True),
        sa.Column("filas_afectadas", sa.Integer, nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
    )

    op.create_index(
        "ix_audit_log_tenant_fecha",
        "audit_log",
        ["tenant_id", sa.text("fecha_hora DESC")],
    )
    op.create_index(
        "ix_audit_log_tenant_actor",
        "audit_log",
        ["tenant_id", "actor_id"],
    )

    # Trigger append-only: rechaza UPDATE y DELETE a nivel DB
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION audit_log_immutable()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
        END;
        $$;
    """))
    conn.execute(sa.text("""
        CREATE TRIGGER trg_audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log"))
    conn.execute(sa.text("DROP FUNCTION IF EXISTS audit_log_immutable()"))
    op.drop_index("ix_audit_log_tenant_actor", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_fecha", table_name="audit_log")
    op.drop_table("audit_log")
