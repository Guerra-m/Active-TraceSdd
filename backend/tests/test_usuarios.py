"""Tests TDD para usuarios y PII (C-07) — tasks 6.1 a 6.3.

Verifica:
  Usuario (6.2):
    - crear exitoso (201), campos sin PII en respuesta
    - PII cifrada en DB (raw query)
    - email duplicado → 409
    - COORDINADOR recibe 403 (sin usuarios:gestionar)
    - aislamiento multi-tenant
    - soft delete (204) + desaparece del listado

  Endpoint PII (6.3):
    - ADMIN accede y recibe PII desencriptada
    - audit_log registra USUARIO_VER_PII

TDD Evidence:
| Task | Layer  | Safety Net   | RED | GREEN | TRIANGULATE |
|------|--------|--------------|-----|-------|-------------|
| 6.2  | Integr | ✅ 144/144   | ✅  | ✅    | ✅ 6 cases  |
| 6.3  | Integr | ✅ 144/144   | ✅  | ✅    | ✅ 2 cases  |
"""

import hashlib
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Fixtures — Task 6.1
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Usuarios A", slug="tenant-usu-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Usuarios B", slug="tenant-usu-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    from app.core.encryption import encrypt
    from app.core.security import create_access_token, hash_password
    from app.models.rol import Rol
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from sqlalchemy import select

    email = f"{email_prefix}@test.com"
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.lower().strip().encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()

    result = await db_session.execute(select(Rol).where(Rol.code == rol_code))
    rol = result.scalar_one()

    ur = UsuarioRol(
        tenant_id=tenant.id,
        user_id=u.id,
        rol_id=rol.id,
        valid_from=date.today(),
        valid_until=None,
    )
    db_session.add(ur)
    await db_session.flush()
    await db_session.commit()

    token = create_access_token(data={
        "sub": str(u.id),
        "tenant_id": str(tenant.id),
        "type": "access",
    })
    return u, token


# ============================================================================
# USUARIO — Task 6.2
# ============================================================================


@pytest.mark.asyncio
async def test_usuario_create_201_sin_pii_en_respuesta(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /admin/usuarios crea usuario y respuesta NO incluye dni/cuil/cbu."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_u1", "ADMIN")

    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={
            "email": "docente1@test.com",
            "password": "Pass1234!",
            "nombre": "Ana",
            "apellidos": "García",
            "dni": "12345678",
            "cuil": "20123456789",
            "legajo": "L001",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["nombre"] == "Ana"
    assert data["apellidos"] == "García"
    assert data["legajo"] == "L001"
    assert data["tenant_id"] == str(tenant_a.id)
    # PII NO debe aparecer en la respuesta estándar
    assert "dni" not in data
    assert "cuil" not in data
    assert "cbu" not in data


@pytest.mark.asyncio
async def test_usuario_pii_cifrada_en_db(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: dni almacenado cifrado (no plaintext) en la columna DB."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_u2", "ADMIN")

    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={"email": "docente2@test.com", "password": "Pass1234!", "dni": "99887766"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    user_id = resp.json()["id"]

    # Query raw a la DB
    result = await db_session.execute(
        text("SELECT dni_encrypted FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    assert row is not None
    # Debe ser un ciphertext AES-GCM (tiene ':' de separador nonce:data)
    assert row[0] != "99887766"
    assert ":" in row[0]


@pytest.mark.asyncio
async def test_usuario_email_duplicado_409(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: email duplicado en mismo tenant → 409."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_u3", "ADMIN")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "dup@test.com", "password": "Pass1234!"}

    resp1 = await async_client.post("/api/v1/admin/usuarios", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/api/v1/admin/usuarios", json=payload, headers=headers)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_usuario_coordinador_recibe_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: COORDINADOR no tiene usuarios:gestionar → 403."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "coord_u4", "COORDINADOR")

    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={"email": "nuevo@test.com", "password": "Pass1234!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_usuario_aislamiento_multi_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: ADMIN del tenant A no ve usuarios del tenant B."""
    _, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_u5a", "ADMIN")
    _, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_u5b", "ADMIN")

    # Crear usuario en tenant B
    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={"email": "solo_b@test.com", "password": "Pass1234!"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 201
    user_b_id = resp.json()["id"]

    # ADMIN de tenant A no puede verlo
    resp_get = await async_client.get(
        f"/api/v1/admin/usuarios/{user_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_get.status_code == 404


@pytest.mark.asyncio
async def test_usuario_soft_delete_204(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: DELETE devuelve 204 y el usuario desaparece del listado."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_u6", "ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    # Crear
    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={"email": "todelete@test.com", "password": "Pass1234!"},
        headers=headers,
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # Borrar
    resp_del = await async_client.delete(
        f"/api/v1/admin/usuarios/{user_id}", headers=headers
    )
    assert resp_del.status_code == 204

    # No encontrable por GET
    resp_get = await async_client.get(
        f"/api/v1/admin/usuarios/{user_id}", headers=headers
    )
    assert resp_get.status_code == 404


# ============================================================================
# ENDPOINT PII — Task 6.3
# ============================================================================


@pytest.mark.asyncio
async def test_pii_endpoint_retorna_campos_descifrados(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: GET /admin/usuarios/{id}/pii retorna dni/cuil desencriptados."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_pii1", "ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={
            "email": "pii_user@test.com",
            "password": "Pass1234!",
            "dni": "11223344",
            "cuil": "27112233448",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    resp_pii = await async_client.get(
        f"/api/v1/admin/usuarios/{user_id}/pii", headers=headers
    )
    assert resp_pii.status_code == 200, resp_pii.text
    data = resp_pii.json()
    assert data["dni"] == "11223344"
    assert data["cuil"] == "27112233448"


@pytest.mark.asyncio
async def test_pii_endpoint_registra_audit_log(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: GET /pii registra entrada USUARIO_VER_PII en audit_log."""
    from sqlalchemy import select
    from app.models.audit_log import AuditLog

    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_pii2", "ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.post(
        "/api/v1/admin/usuarios",
        json={"email": "pii_audit@test.com", "password": "Pass1234!"},
        headers=headers,
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    await async_client.get(f"/api/v1/admin/usuarios/{user_id}/pii", headers=headers)

    # Verificar que hay una entrada en audit_log con la acción correcta
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.accion == "USUARIO_VER_PII",
            AuditLog.tenant_id == tenant_a.id,
        )
    )
    entries = result.scalars().all()
    assert len(entries) >= 1
    assert str(entries[-1].actor_id) == str(admin.id)
