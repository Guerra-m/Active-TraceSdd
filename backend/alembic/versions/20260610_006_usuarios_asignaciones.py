"""usuarios_asignaciones

Revision ID: 20260610_006
Revises: 20260610_005
Create Date: 2026-06-10

Migración 006 — C-07 usuarios-y-asignaciones
Extiende la tabla `users` con campos de perfil docente (PII cifrada en capa app)
y crea la tabla `asignaciones` (usuario ↔ rol ↔ contexto académico + vigencia).

Todos los campos PII se almacenan cifrados a nivel aplicación (AES-256-GCM).
Las columnas se agregan como nullable para evitar table-lock en producción
(ALTER TABLE nullable es O(1) en PostgreSQL — solo metadata).

upgrade  : ALTER TABLE users ADD COLUMNs + CREATE TABLE asignaciones
downgrade: DROP TABLE asignaciones + ALTER TABLE users DROP COLUMNs
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_006"
down_revision = "20260610_005"
branch_labels = None
depends_on = None

_ROL_CHECK = "rol IN ('ALUMNO','TUTOR','PROFESOR','COORDINADOR','NEXO','ADMIN','FINANZAS')"
_ESTADO_CHECK = "estado IN ('Activo', 'Inactivo')"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Extender tabla users con campos de perfil docente
    # ------------------------------------------------------------------
    op.add_column("users", sa.Column("nombre", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("apellidos", sa.String(200), nullable=True))
    # PII — almacenados cifrados con AES-256-GCM a nivel aplicación
    op.add_column("users", sa.Column("dni_encrypted", sa.Text, nullable=True))
    op.add_column("users", sa.Column("cuil_encrypted", sa.Text, nullable=True))
    op.add_column("users", sa.Column("cbu_encrypted", sa.Text, nullable=True))
    op.add_column("users", sa.Column("alias_cbu_encrypted", sa.Text, nullable=True))
    # Datos no-PII
    op.add_column("users", sa.Column("banco", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("regional", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("legajo", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("legajo_profesional", sa.String(50), nullable=True))
    op.add_column(
        "users",
        sa.Column("facturador", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activo"),
    )
    op.create_check_constraint("ck_users_estado", "users", _ESTADO_CHECK)

    # ------------------------------------------------------------------
    # 2. Tabla asignaciones (usuario ↔ rol ↔ contexto académico + vigencia)
    # ------------------------------------------------------------------
    op.create_table(
        "asignaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "comisiones",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "responsable_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(_ROL_CHECK, name="ck_asignaciones_rol"),
    )
    op.create_index("ix_asignaciones_tenant", "asignaciones", ["tenant_id"])
    op.create_index("ix_asignaciones_tenant_usuario", "asignaciones", ["tenant_id", "usuario_id"])
    op.create_index("ix_asignaciones_tenant_materia", "asignaciones", ["tenant_id", "materia_id"])
    op.create_index("ix_asignaciones_tenant_rol", "asignaciones", ["tenant_id", "rol"])


def downgrade() -> None:
    op.drop_index("ix_asignaciones_tenant_rol", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant_materia", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant_usuario", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant", table_name="asignaciones")
    op.drop_table("asignaciones")

    op.drop_constraint("ck_users_estado", "users", type_="check")
    for col in [
        "estado", "facturador", "legajo_profesional", "legajo",
        "regional", "banco", "alias_cbu_encrypted", "cbu_encrypted",
        "cuil_encrypted", "dni_encrypted", "apellidos", "nombre",
    ]:
        op.drop_column("users", col)
