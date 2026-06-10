"""padron

Revision ID: 20260610_007
Revises: 20260610_006
Create Date: 2026-06-10

Migración 007 — C-09 padron-ingesta-moodle
Crea las tablas `version_padron` y `entrada_padron` para el padrón versionado
de alumnos por materia×cohorte×tenant.

Modelo versionado (E6 del modelo de datos):
  - version_padron: cabecera de cada importación; activa=True para la versión vigente
  - entrada_padron: cada alumno del padrón; email cifrado AES-256-GCM a nivel app

upgrade  : CREATE TABLE version_padron + CREATE TABLE entrada_padron
downgrade: DROP TABLE entrada_padron → DROP TABLE version_padron
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_007"
down_revision = "20260610_006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla version_padron (cabecera de cada importación)
    # ------------------------------------------------------------------
    op.create_table(
        "version_padron",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activa", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_version_padron_tenant",
        "version_padron", ["tenant_id"],
    )
    op.create_index(
        "ix_version_padron_tenant_materia_cohorte",
        "version_padron", ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_version_padron_tenant_activa",
        "version_padron", ["tenant_id", "materia_id", "cohorte_id", "activa"],
    )

    # ------------------------------------------------------------------
    # 2. Tabla entrada_padron (filas del padrón por alumno)
    # ------------------------------------------------------------------
    op.create_table(
        "entrada_padron",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("version_padron.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("apellidos", sa.String(200), nullable=False),
        # PII — cifrado AES-256-GCM a nivel aplicación
        sa.Column("email_encrypted", sa.Text, nullable=False),
        sa.Column("comision", sa.String(100), nullable=True),
        sa.Column("regional", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_entrada_padron_tenant_version", "entrada_padron", ["tenant_id", "version_id"])
    op.create_index("ix_entrada_padron_tenant_usuario", "entrada_padron", ["tenant_id", "usuario_id"])

    # ------------------------------------------------------------------
    # 3. Seed: permiso padron:importar + asignaciones a roles
    # ------------------------------------------------------------------
    def _uid(key: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, key))

    perm_id = _uid("perm:padron:importar")
    bind = op.get_bind()

    bind.execute(
        sa.text(
            "INSERT INTO permisos (id, code, description, is_active, created_at) "
            "VALUES (:id, :code, :desc, true, now()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": perm_id, "code": "padron:importar", "desc": "Importar/gestionar padrón de alumnos por materia"},
    )

    for rol_code, is_own in [("PROFESOR", True), ("COORDINADOR", False), ("ADMIN", False)]:
        rol_id = _uid(f"role:{rol_code}")
        rp_id = _uid(f"rp:{rol_code}:padron:importar")
        bind.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, is_own_resource, created_at, updated_at) "
                "VALUES (:id, NULL, :rol_id, :perm_id, :is_own, now(), now()) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": rp_id, "rol_id": rol_id, "perm_id": perm_id, "is_own": is_own},
        )


def downgrade() -> None:
    op.drop_index("ix_entrada_padron_tenant_usuario", table_name="entrada_padron")
    op.drop_index("ix_entrada_padron_tenant_version", table_name="entrada_padron")
    op.drop_table("entrada_padron")

    op.drop_index("ix_version_padron_tenant_activa", table_name="version_padron")
    op.drop_index("ix_version_padron_tenant_materia_cohorte", table_name="version_padron")
    op.drop_index("ix_version_padron_tenant", table_name="version_padron")
    op.drop_table("version_padron")
