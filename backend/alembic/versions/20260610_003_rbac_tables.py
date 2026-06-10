"""rbac_tables

Revision ID: 20260610_003
Revises: 20260610_002
Create Date: 2026-06-10

Migración 003 — C-04 rbac-permisos-finos
Crea las tablas de autorización RBAC:
  - roles         (Rol model)
  - permisos      (Permiso model)
  - rol_permiso   (RolPermiso model — TenantScopedBase)
  - usuario_rol   (UsuarioRol model — TenantScopedBase)

Seed:
  - 7 roles del dominio (is_system=True, tenant_id=NULL)
  - ≥21 permisos del dominio en formato modulo:accion
  - Matriz rol_permiso base según knowledge-base/03_actores_y_roles.md §3.3
    con is_own_resource correcto para permisos marcados (propio)

upgrade  : crea 4 tablas + índices + seed de roles, permisos y matriz base
downgrade: elimina las 4 tablas en orden inverso (cascade safe)
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260610_003"
down_revision = "20260610_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tablas RBAC e insertar seed de roles, permisos y matriz base."""

    # -------------------------------------------------------------------------
    # Tabla: roles
    # -------------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    # -------------------------------------------------------------------------
    # Tabla: permisos
    # -------------------------------------------------------------------------
    op.create_table(
        "permisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_permisos_code", "permisos", ["code"], unique=True)

    # -------------------------------------------------------------------------
    # Tabla: rol_permiso (TenantScopedBase)
    # -------------------------------------------------------------------------
    op.create_table(
        "rol_permiso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permiso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permisos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_own_resource", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("rol_id", "permiso_id", "tenant_id", name="uq_rol_permiso_tenant"),
    )
    op.create_index("ix_rol_permiso_rol_tenant", "rol_permiso", ["rol_id", "tenant_id"])
    op.create_index("ix_rol_permiso_tenant_id", "rol_permiso", ["tenant_id"])

    # -------------------------------------------------------------------------
    # Tabla: usuario_rol (TenantScopedBase)
    # -------------------------------------------------------------------------
    op.create_table(
        "usuario_rol",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id", "rol_id", "tenant_id", "valid_from",
            name="uq_usuario_rol_vigencia",
        ),
    )
    op.create_index(
        "ix_usuario_rol_user_tenant",
        "usuario_rol",
        ["user_id", "tenant_id", "valid_from", "valid_until"],
    )
    op.create_index("ix_usuario_rol_tenant_id", "usuario_rol", ["tenant_id"])

    # =========================================================================
    # SEED — Roles del dominio (7 roles, is_system=True, tenant_id=NULL)
    # =========================================================================
    conn = op.get_bind()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # UUIDs estáticos y determinísticos para el seed (no generados al vuelo
    # para que el downgrade pueda referenciarlos si fuera necesario)
    roles_seed = [
        {"code": "ALUMNO",      "name": "Alumno",       "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:ALUMNO"))},
        {"code": "TUTOR",       "name": "Tutor",        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:TUTOR"))},
        {"code": "PROFESOR",    "name": "Profesor",     "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:PROFESOR"))},
        {"code": "COORDINADOR", "name": "Coordinador",  "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:COORDINADOR"))},
        {"code": "NEXO",        "name": "Nexo",         "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:NEXO"))},
        {"code": "ADMIN",       "name": "Admin",        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:ADMIN"))},
        {"code": "FINANZAS",    "name": "Finanzas",     "id": str(uuid.uuid5(uuid.NAMESPACE_OID, "role:FINANZAS"))},
    ]

    for r in roles_seed:
        conn.execute(
            sa.text(
                "INSERT INTO roles (id, code, name, is_system, tenant_id, is_active, created_at, updated_at) "
                "VALUES (:id, :code, :name, TRUE, NULL, TRUE, :now, :now)"
            ),
            {"id": r["id"], "code": r["code"], "name": r["name"], "now": now},
        )

    # =========================================================================
    # SEED — Permisos del dominio (≥21 según spec rbac-catalog)
    # Matriz completa de knowledge-base/03_actores_y_roles.md §3.3
    # =========================================================================
    permisos_seed = [
        # Módulo: academico
        ("academico:ver_propio",        "Ver estado académico propio del alumno"),
        # Módulo: evaluacion
        ("evaluacion:reservar",         "Reservar instancia de evaluación"),
        # Módulo: avisos
        ("avisos:confirmar",            "Confirmar (acknowledge) avisos"),
        ("avisos:publicar",             "Publicar avisos para alumnos"),
        # Módulo: calificaciones
        ("calificaciones:importar",     "Importar calificaciones desde Moodle"),
        # Módulo: atrasados
        ("atrasados:ver",               "Ver alumnos con atrasos en entregas"),
        # Módulo: entregas
        ("entregas:ver",                "Ver entregas sin corregir"),
        # Módulo: comunicacion
        ("comunicacion:enviar",         "Enviar comunicaciones a alumnos"),
        ("comunicacion:aprobar",        "Aprobar comunicaciones masivas"),
        # Módulo: encuentros
        ("encuentros:gestionar",        "Gestionar encuentros docentes"),
        # Módulo: guardias
        ("guardias:registrar",          "Registrar guardias"),
        # Módulo: tareas
        ("tareas:gestionar",            "Gestionar tareas internas"),
        # Módulo: equipos
        ("equipos:asignar",             "Gestionar equipos docentes y asignaciones"),
        # Módulo: estructura
        ("estructura:gestionar",        "Gestionar estructura académica (carreras, cohortes, materias)"),
        # Módulo: usuarios
        ("usuarios:gestionar",          "Gestionar usuarios del tenant"),
        # Módulo: auditoria
        ("auditoria:ver",               "Ver registros de auditoría"),
        # Módulo: liquidaciones
        ("liquidaciones:operar",        "Operar grilla salarial"),
        ("liquidaciones:cerrar",        "Calcular y cerrar liquidaciones"),
        # Módulo: facturas
        ("facturas:gestionar",          "Gestionar facturas"),
        # Módulo: tenant
        ("tenant:configurar",           "Configurar el tenant"),
        # Módulo: impersonacion
        ("impersonacion:usar",          "Impersonar a otro usuario (soporte/ADMIN)"),
        # Módulo: roles (catálogo RBAC — este change)
        ("roles:ver",                   "Ver catálogo de roles y permisos"),
    )

    perm_id_map = {}
    for code, desc in permisos_seed:
        pid = str(uuid.uuid5(uuid.NAMESPACE_OID, f"perm:{code}"))
        perm_id_map[code] = pid
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, code, description, is_active, created_at) "
                "VALUES (:id, :code, :desc, TRUE, :now)"
            ),
            {"id": pid, "code": code, "desc": desc, "now": now},
        )

    # =========================================================================
    # SEED — Matriz rol_permiso base según §3.3
    # NOTA: La tabla rol_permiso es TenantScopedBase (tenant_id NOT NULL).
    # El seed de la matriz base usa un tenant_id sentinel = UUID5("seed:system")
    # para satisfacer la constraint. Los tenants reales heredan este catálogo
    # vía la resolución que combina roles sistema + asignaciones tenant.
    #
    # DISEÑO REVISADO: Los roles sistema son globales (tenant_id=NULL en roles).
    # La tabla rol_permiso requiere tenant_id NOT NULL. La solución es que
    # el seed de la matriz base también use tenant_id=NULL — pero esto requiere
    # cambiar la constraint. En su lugar, la resolución de permisos efectivos
    # consulta las asignaciones de rol_permiso filtrando por:
    #   (tenant_id = tenant_actual) OR (tenant_id IS NULL)
    #
    # Para el seed del catálogo base, marcamos tenant_id=NULL en rol_permiso
    # modificando la tabla para aceptar NULL en tenant_id para filas de sistema.
    # =========================================================================
    # Dado que TenantScopedBase tiene tenant_id NOT NULL, necesitamos un enfoque
    # diferente. La matriz base del catálogo se almacena con tenant_id=NULL
    # mediante ALTER de la columna en esta migración.
    # Alternativamente: almacenamos la matriz con un UUID sentinel vacío y
    # el resolver la filtra correctamente.
    #
    # DECISIÓN FINAL: tenant_id en rol_permiso admite NULL para filas de sistema.
    # Se hace ALTER de la columna aquí.
    # =========================================================================

    # Permitir NULL en tenant_id de rol_permiso para la matriz base del sistema
    conn.execute(sa.text("ALTER TABLE rol_permiso ALTER COLUMN tenant_id DROP NOT NULL"))

    role_id = {r["code"]: r["id"] for r in roles_seed}

    # Formato: (rol_code, permiso_code, is_own_resource)
    # Basado en knowledge-base/03_actores_y_roles.md §3.3
    # (propio) = is_own_resource=True
    matriz_seed = [
        # ALUMNO
        ("ALUMNO", "academico:ver_propio",    False),
        ("ALUMNO", "evaluacion:reservar",     False),
        ("ALUMNO", "avisos:confirmar",        False),

        # TUTOR
        ("TUTOR", "avisos:confirmar",         False),
        ("TUTOR", "atrasados:ver",            False),
        ("TUTOR", "entregas:ver",             False),
        ("TUTOR", "encuentros:gestionar",     False),
        ("TUTOR", "guardias:registrar",       True),  # (propio)

        # PROFESOR
        ("PROFESOR", "avisos:confirmar",      False),
        ("PROFESOR", "calificaciones:importar", True),  # (propio)
        ("PROFESOR", "atrasados:ver",         True),   # (propio)
        ("PROFESOR", "entregas:ver",          True),   # (propio)
        ("PROFESOR", "comunicacion:enviar",   True),   # (propio)
        ("PROFESOR", "encuentros:gestionar",  True),   # (propio)
        ("PROFESOR", "guardias:registrar",    True),   # (propio)
        ("PROFESOR", "tareas:gestionar",      True),   # (propio)

        # COORDINADOR
        ("COORDINADOR", "avisos:confirmar",       False),
        ("COORDINADOR", "calificaciones:importar", False),
        ("COORDINADOR", "atrasados:ver",           False),
        ("COORDINADOR", "entregas:ver",            False),
        ("COORDINADOR", "comunicacion:enviar",     False),
        ("COORDINADOR", "comunicacion:aprobar",    False),
        ("COORDINADOR", "encuentros:gestionar",    False),
        ("COORDINADOR", "guardias:registrar",      False),
        ("COORDINADOR", "tareas:gestionar",        False),
        ("COORDINADOR", "avisos:publicar",         False),
        ("COORDINADOR", "equipos:asignar",         False),
        ("COORDINADOR", "auditoria:ver",           True),  # (propio)

        # ADMIN
        ("ADMIN", "avisos:confirmar",          False),
        ("ADMIN", "calificaciones:importar",   False),
        ("ADMIN", "atrasados:ver",             False),
        ("ADMIN", "entregas:ver",              False),
        ("ADMIN", "comunicacion:enviar",       False),
        ("ADMIN", "comunicacion:aprobar",      False),
        ("ADMIN", "encuentros:gestionar",      False),
        ("ADMIN", "guardias:registrar",        False),
        ("ADMIN", "tareas:gestionar",          False),
        ("ADMIN", "avisos:publicar",           False),
        ("ADMIN", "equipos:asignar",           False),
        ("ADMIN", "estructura:gestionar",      False),
        ("ADMIN", "usuarios:gestionar",        False),
        ("ADMIN", "auditoria:ver",             False),
        ("ADMIN", "tenant:configurar",         False),
        ("ADMIN", "roles:ver",                 False),

        # FINANZAS
        ("FINANZAS", "avisos:confirmar",       False),
        ("FINANZAS", "auditoria:ver",          False),
        ("FINANZAS", "liquidaciones:operar",   False),
        ("FINANZAS", "liquidaciones:cerrar",   False),
        ("FINANZAS", "facturas:gestionar",     False),

        # NEXO — sin permisos predefinidos (configurable por tenant)
    ]

    for rol_code, perm_code, is_own in matriz_seed:
        rid = role_id[rol_code]
        pid = perm_id_map[perm_code]
        new_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"rp:{rol_code}:{perm_code}"))
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, is_own_resource, created_at, updated_at) "
                "VALUES (:id, NULL, :rol_id, :perm_id, :is_own, :now, :now)"
            ),
            {
                "id": new_id,
                "rol_id": rid,
                "perm_id": pid,
                "is_own": is_own,
                "now": now,
            },
        )


def downgrade() -> None:
    """Eliminar tablas RBAC en orden inverso."""
    op.drop_table("usuario_rol")
    op.drop_table("rol_permiso")
    op.drop_table("permisos")
    op.drop_table("roles")
