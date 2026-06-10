"""estructura_academica

Revision ID: 20260610_005
Revises: 20260610_004
Create Date: 2026-06-10

Migración 005 — C-06 estructura-academica
Crea tablas raíz del dominio académico:
  - carreras   : catálogo de carreras por tenant (E1)
  - cohortes   : cohortes temporales por carrera (E2)
  - materias   : catálogo plano de materias por tenant (E3, ADR-006)

Añade la FK diferida de audit_log.materia_id → materias.id (diferida en C-05
para evitar dependencia circular con la tabla 'materias' que aún no existía).

upgrade  : crea carreras, cohortes, materias + FK en audit_log
downgrade: elimina FK en audit_log, luego cohortes, materias, carreras
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_005"
down_revision = "20260610_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla carreras
    # ------------------------------------------------------------------
    op.create_table(
        "carreras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_carreras_tenant_codigo"),
        sa.CheckConstraint("estado IN ('Activa', 'Inactiva')", name="ck_carreras_estado"),
    )
    op.create_index("ix_carreras_tenant", "carreras", ["tenant_id"])

    # ------------------------------------------------------------------
    # 2. Tabla cohortes (depende de carreras)
    # ------------------------------------------------------------------
    op.create_table(
        "cohortes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("anio", sa.SmallInteger, nullable=False),
        sa.Column("vig_desde", sa.Date, nullable=False),
        sa.Column("vig_hasta", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name="uq_cohortes_tenant_carrera_nombre"
        ),
    )

    # ------------------------------------------------------------------
    # 3. Tabla materias
    # ------------------------------------------------------------------
    op.create_table(
        "materias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_materias_tenant_codigo"),
        sa.CheckConstraint("estado IN ('Activa', 'Inactiva')", name="ck_materias_estado"),
    )
    op.create_index("ix_materias_tenant", "materias", ["tenant_id"])

    # ------------------------------------------------------------------
    # 4. FK diferida: audit_log.materia_id → materias.id
    # ------------------------------------------------------------------
    op.create_foreign_key(
        "fk_audit_materia",
        "audit_log",
        "materias",
        ["materia_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Eliminar FK en audit_log primero (referencia a materias)
    op.drop_constraint("fk_audit_materia", "audit_log", type_="foreignkey")

    # Cohortes depende de carreras → eliminar antes
    op.drop_table("cohortes")

    op.drop_index("ix_materias_tenant", table_name="materias")
    op.drop_table("materias")

    op.drop_index("ix_carreras_tenant", table_name="carreras")
    op.drop_table("carreras")
