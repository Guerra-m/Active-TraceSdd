"""017 liquidaciones — tablas salarios_base, salarios_plus, liquidaciones, facturas.

Implementa C-18 liquidaciones-y-honorarios.

Revision ID: 20260611_017
Revises: 20260611_016
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260611_017"
down_revision = "20260611_016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- salarios_base ---
    op.create_table(
        "salarios_base",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "rol IN ('ALUMNO','TUTOR','PROFESOR','COORDINADOR','NEXO','ADMIN','FINANZAS')",
            name="ck_salarios_base_rol",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_salarios_base_tenant_rol", "salarios_base", ["tenant_id", "rol"])
    op.create_index("ix_salarios_base_tenant_desde", "salarios_base", ["tenant_id", "desde"])

    # --- salarios_plus ---
    op.create_table(
        "salarios_plus",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.String(200), nullable=False, server_default=""),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "rol IN ('ALUMNO','TUTOR','PROFESOR','COORDINADOR','NEXO','ADMIN','FINANZAS')",
            name="ck_salarios_plus_rol",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_salarios_plus_tenant_grupo_rol", "salarios_plus", ["tenant_id", "grupo", "rol"]
    )
    op.create_index("ix_salarios_plus_tenant_desde", "salarios_plus", ["tenant_id", "desde"])

    # --- liquidaciones ---
    op.create_table(
        "liquidaciones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("comisiones", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("monto_base", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("monto_plus", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("es_nexo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("excluido_por_factura", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Abierta"),
        sa.CheckConstraint("estado IN ('Abierta', 'Cerrada')", name="ck_liquidaciones_estado"),
        sa.CheckConstraint(
            "periodo ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_liquidaciones_periodo_formato"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_liquidaciones_tenant_periodo", "liquidaciones", ["tenant_id", "periodo"]
    )
    op.create_index(
        "ix_liquidaciones_tenant_usuario", "liquidaciones", ["tenant_id", "usuario_id"]
    )
    op.create_index(
        "ix_liquidaciones_tenant_cohorte", "liquidaciones", ["tenant_id", "cohorte_id"]
    )

    # --- facturas ---
    op.create_table(
        "facturas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("detalle", sa.String(500), nullable=False, server_default=""),
        sa.Column("archivo_ref", sa.String(500), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("fecha_carga", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_pago", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "estado IN ('Pendiente', 'Abonada')", name="ck_facturas_estado"
        ),
        sa.CheckConstraint(
            "periodo ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_facturas_periodo_formato"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_facturas_tenant_periodo", "facturas", ["tenant_id", "periodo"])
    op.create_index("ix_facturas_tenant_usuario", "facturas", ["tenant_id", "usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_facturas_tenant_usuario", table_name="facturas")
    op.drop_index("ix_facturas_tenant_periodo", table_name="facturas")
    op.drop_table("facturas")

    op.drop_index("ix_liquidaciones_tenant_cohorte", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_tenant_usuario", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_tenant_periodo", table_name="liquidaciones")
    op.drop_table("liquidaciones")

    op.drop_index("ix_salarios_plus_tenant_desde", table_name="salarios_plus")
    op.drop_index("ix_salarios_plus_tenant_grupo_rol", table_name="salarios_plus")
    op.drop_table("salarios_plus")

    op.drop_index("ix_salarios_base_tenant_desde", table_name="salarios_base")
    op.drop_index("ix_salarios_base_tenant_rol", table_name="salarios_base")
    op.drop_table("salarios_base")
