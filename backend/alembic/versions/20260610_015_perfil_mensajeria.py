"""015 perfil_mensajeria — hilos_mensaje y mensajes_internos.

Revision ID: 20260610_015
Revises: 20260610_014
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa

revision = "20260610_015"
down_revision = "20260610_014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hilos_mensaje",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asunto", sa.String(200), nullable=False),
        sa.Column("remitente_id", sa.UUID(), nullable=False),
        sa.Column("destinatario_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hilos_tenant_dest", "hilos_mensaje", ["tenant_id", "destinatario_id"])
    op.create_index("ix_hilos_tenant_rem", "hilos_mensaje", ["tenant_id", "remitente_id"])

    op.create_table(
        "mensajes_internos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hilo_id", sa.UUID(), nullable=False),
        sa.Column("autor_id", sa.UUID(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mensajes_hilo", "mensajes_internos", ["tenant_id", "hilo_id"])


def downgrade() -> None:
    op.drop_index("ix_mensajes_hilo", table_name="mensajes_internos")
    op.drop_table("mensajes_internos")
    op.drop_index("ix_hilos_tenant_dest", table_name="hilos_mensaje")
    op.drop_index("ix_hilos_tenant_rem", table_name="hilos_mensaje")
    op.drop_table("hilos_mensaje")
