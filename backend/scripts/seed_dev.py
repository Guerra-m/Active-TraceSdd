"""Script de seed para desarrollo/demo.

Crea un tenant de prueba con un usuario por cada rol del dominio.
Seguro de re-ejecutar: usa INSERT OR SKIP (on_conflict_do_nothing).

Uso:
    cd backend
    python scripts/seed_dev.py

Requiere que las migraciones ya estén aplicadas:
    alembic upgrade head

Usuarios creados:
    admin@trace.dev         / Trace1234!  → ADMIN
    coordinador@trace.dev   / Trace1234!  → COORDINADOR
    profesor@trace.dev      / Trace1234!  → PROFESOR
    finanzas@trace.dev      / Trace1234!  → FINANZAS
    alumno@trace.dev        / Trace1234!  → ALUMNO
"""

import asyncio
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Asegura que 'backend/' esté en el path para importar 'app'
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.core import database as _db
from app.core.database import init_engine
from app.core.encryption import encrypt
from app.core.rbac_seed import get_roles_seed, get_permisos_seed, get_matriz_seed
from app.core.security import hash_email, hash_password

# ---------------------------------------------------------------------------
# Datos del tenant de demo
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TENANT_NAME = "UTN Demo"
TENANT_SLUG = "utn-demo"

PASSWORD = "Trace1234!"

USERS = [
    {
        "email": "admin@trace.dev",
        "nombre": "Admin",
        "apellidos": "Sistema",
        "rol_code": "ADMIN",
    },
    {
        "email": "coordinador@trace.dev",
        "nombre": "Carlos",
        "apellidos": "Coordinador",
        "rol_code": "COORDINADOR",
    },
    {
        "email": "profesor@trace.dev",
        "nombre": "María",
        "apellidos": "Profesora",
        "rol_code": "PROFESOR",
    },
    {
        "email": "finanzas@trace.dev",
        "nombre": "Laura",
        "apellidos": "Finanzas",
        "rol_code": "FINANZAS",
    },
    {
        "email": "alumno@trace.dev",
        "nombre": "Juan",
        "apellidos": "Alumno",
        "rol_code": "ALUMNO",
    },
]


def _uid(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, key))


async def seed() -> None:
    now = datetime.now(timezone.utc)
    today = date.today()

    async with _db.async_session_factory() as session:
        # ----------------------------------------------------------------
        # 1. Tenant
        # ----------------------------------------------------------------
        await session.execute(
            text("""
                INSERT INTO tenants (id, name, slug, is_active, created_at, updated_at)
                VALUES (:id, :name, :slug, true, :now, :now)
                ON CONFLICT DO NOTHING
            """),
            {"id": str(TENANT_ID), "name": TENANT_NAME, "slug": TENANT_SLUG, "now": now},
        )
        print(f"  tenant: {TENANT_SLUG} ({TENANT_ID})")

        # ----------------------------------------------------------------
        # 2. RBAC seed — roles, permisos, matriz
        # ----------------------------------------------------------------
        for r in get_roles_seed():
            await session.execute(
                text("""
                    INSERT INTO roles (id, code, name, is_system, tenant_id, is_active, created_at, updated_at)
                    VALUES (:id, :code, :name, true, NULL, true, :now, :now)
                    ON CONFLICT DO NOTHING
                """),
                {**r, "now": now},
            )

        for p in get_permisos_seed():
            await session.execute(
                text("""
                    INSERT INTO permisos (id, code, description, is_active, created_at)
                    VALUES (:id, :code, :description, true, :now)
                    ON CONFLICT DO NOTHING
                """),
                {**p, "now": now},
            )

        for rol_code, perm_code, is_own in get_matriz_seed():
            rp_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"rp:{rol_code}:{perm_code}"))
            await session.execute(
                text("""
                    INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, is_own_resource, created_at, updated_at)
                    VALUES (
                        :id, NULL,
                        (SELECT id FROM roles WHERE code = :rol_code AND tenant_id IS NULL),
                        (SELECT id FROM permisos WHERE code = :perm_code),
                        :is_own, :now, :now
                    )
                    ON CONFLICT DO NOTHING
                """),
                {"id": rp_id, "rol_code": rol_code, "perm_code": perm_code, "is_own": is_own, "now": now},
            )
        print("  rbac: roles, permisos y matriz insertados")

        # ----------------------------------------------------------------
        # 3. Usuarios + asignación de rol
        # ----------------------------------------------------------------
        password_hash = hash_password(PASSWORD)

        for u in USERS:
            user_id = uuid.uuid5(uuid.NAMESPACE_OID, f"dev:user:{u['email']}")
            email_enc = encrypt(u["email"])
            email_hash = hash_email(u["email"])

            await session.execute(
                text("""
                    INSERT INTO users (
                        id, tenant_id, email_encrypted, email_hash, password_hash,
                        is_active, totp_enabled, nombre, apellidos,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant_id, :email_enc, :email_hash, :pwd_hash,
                        true, false, :nombre, :apellidos,
                        :now, :now
                    )
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": str(user_id),
                    "tenant_id": str(TENANT_ID),
                    "email_enc": email_enc,
                    "email_hash": email_hash,
                    "pwd_hash": password_hash,
                    "nombre": u["nombre"],
                    "apellidos": u["apellidos"],
                    "now": now,
                },
            )

            ur_id = uuid.uuid5(uuid.NAMESPACE_OID, f"dev:ur:{u['email']}:{u['rol_code']}")
            await session.execute(
                text("""
                    INSERT INTO usuario_rol (
                        id, tenant_id, user_id, rol_id, valid_from, valid_until,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant_id, :user_id,
                        (SELECT id FROM roles WHERE code = :rol_code AND tenant_id IS NULL),
                        :valid_from, NULL,
                        :now, :now
                    )
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": str(ur_id),
                    "tenant_id": str(TENANT_ID),
                    "user_id": str(user_id),
                    "rol_code": u["rol_code"],
                    "valid_from": today,
                    "now": now,
                },
            )
            print(f"  user: {u['email']} → {u['rol_code']}")

        await session.commit()

    print("\nSeed completado.")
    print(f"\nTenant: {TENANT_NAME}  (slug: {TENANT_SLUG})")
    print(f"Password para todos los usuarios: {PASSWORD}")
    print()
    print("Usuarios disponibles:")
    for u in USERS:
        print(f"  {u['email']:<30} → {u['rol_code']}")


def main() -> None:
    print(f"\nConectando a: {get_settings().database_url}\n")
    init_engine()
    asyncio.run(seed())


if __name__ == "__main__":
    main()
