"""auth_tables

Revision ID: 20260610_002
Revises: 20260610_001
Create Date: 2026-06-10

Migración 002 — C-03 auth-jwt-2fa
Crea las tablas de autenticación:
  - users                 (User model — TenantScopedBase)
  - refresh_tokens        (RefreshToken model — rotación con hash)
  - password_reset_tokens (PasswordResetToken model — un solo uso)

upgrade  : crea las 3 tablas con sus índices
downgrade: elimina las 3 tablas en orden inverso (cascade safe)
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260610_002"
down_revision = "20260610_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tablas users, refresh_tokens, password_reset_tokens."""

    # -------------------------------------------------------------------------
    # Tabla: users
    # -------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("email_encrypted", sa.String, nullable=False),
        sa.Column("email_hash", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("totp_secret_encrypted", sa.String, nullable=True),
        sa.Column("totp_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email_hash", "users", ["email_hash"], unique=True)
    op.create_index("ix_users_tenant_email_hash", "users", ["tenant_id", "email_hash"], unique=True)

    # -------------------------------------------------------------------------
    # Tabla: refresh_tokens
    # -------------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_tenant_user", "refresh_tokens", ["tenant_id", "user_id"])

    # -------------------------------------------------------------------------
    # Tabla: password_reset_tokens
    # -------------------------------------------------------------------------
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prt_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_prt_tenant_id", "password_reset_tokens", ["tenant_id"])
    op.create_index("ix_prt_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    op.create_index("ix_prt_tenant_user", "password_reset_tokens", ["tenant_id", "user_id"])


def downgrade() -> None:
    """Eliminar tablas de autenticación en orden inverso."""
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
