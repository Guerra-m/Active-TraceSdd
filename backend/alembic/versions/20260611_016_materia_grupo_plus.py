"""016 materia_grupo_plus — campo grupo_plus en tabla materias.

Resuelve PA-22: el tenant ADMIN mapea cada materia a una clave de Plus.
Si es NULL, la materia no genera Plus en liquidaciones.

Revision ID: 20260611_016
Revises: 20260610_015
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa

revision = "20260611_016"
down_revision = "20260610_015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "materias",
        sa.Column("grupo_plus", sa.String(50), nullable=True, server_default=None),
    )
    op.create_index("ix_materias_grupo_plus", "materias", ["tenant_id", "grupo_plus"])


def downgrade() -> None:
    op.drop_index("ix_materias_grupo_plus", table_name="materias")
    op.drop_column("materias", "grupo_plus")
