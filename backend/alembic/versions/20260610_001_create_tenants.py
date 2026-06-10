"""create_tenants

Revision ID: 20260610_001
Revises:
Create Date: 2026-06-10

Migración 001 — C-02 core-models-y-tenancy
Crea la tabla `tenants`, entidad raíz del sistema multi-tenant.

upgrade  : crea tabla tenants
downgrade: elimina tabla tenants (DROP TABLE tenants CASCADE)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260610_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tabla tenants."""
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_tenants_name"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    # Indice en slug para busquedas rapidas
    op.create_index(
        "ix_tenants_slug",
        "tenants",
        ["slug"],
        unique=True,
    )


def downgrade() -> None:
    """Eliminar tabla tenants."""
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
