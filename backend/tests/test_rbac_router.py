"""Tests para los endpoints REST del catálogo RBAC.

Suite TDD (Strict) para C-04 rbac-permisos-finos — tarea 8.10.
Verifica:
  - GET /rbac/roles con usuario ADMIN → 200 con lista de roles
  - GET /rbac/roles sin permiso roles:ver → 403
  - GET /rbac/roles/{rol_id}/permisos con usuario ADMIN → 200
  - Los endpoints existentes (auth, health) siguen funcionando
"""

import hashlib
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    """Seed RBAC para todos los tests de este módulo."""
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant RBAC Router Test", slug="tenant-rbac-router")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    """Crea un usuario con el rol especificado y devuelve (user, token)."""
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from app.core.security import create_access_token, hash_password
    from sqlalchemy import select
    from app.models.rol import Rol

    email = f"{email_prefix}@test.com"
    email_hash = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
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


# ---------------------------------------------------------------------------
# Test 8.10 — GET /rbac/roles con ADMIN → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_roles_as_admin_returns_200(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """ADMIN con permiso roles:ver puede listar roles disponibles."""
    _user, token = await _make_user_with_rol(db_session, tenant, "admin_router", "ADMIN")

    resp = await async_client.get(
        "/api/v1/rbac/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    roles = resp.json()
    assert isinstance(roles, list), "La respuesta debe ser una lista"
    assert len(roles) >= 7, f"Debe haber ≥7 roles, obtenido: {len(roles)}"
    codes = {r["code"] for r in roles}
    assert "ADMIN" in codes
    assert "ALUMNO" in codes


@pytest.mark.asyncio
async def test_get_roles_without_permission_returns_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Usuario sin permiso roles:ver recibe 403."""
    # ALUMNO no tiene el permiso roles:ver
    _user, token = await _make_user_with_rol(db_session, tenant, "alumno_router", "ALUMNO")

    resp = await async_client.get(
        "/api/v1/rbac/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403, f"Esperado 403, obtenido {resp.status_code}: {resp.text}"
    assert "Permiso insuficiente" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_get_roles_unauthenticated_returns_401(async_client: AsyncClient):
    """Sin autenticación → 401."""
    resp = await async_client.get("/api/v1/rbac/roles")
    assert resp.status_code == 401, f"Esperado 401, obtenido {resp.status_code}"


# ---------------------------------------------------------------------------
# Test 8.10 — GET /rbac/roles/{rol_id}/permisos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_rol_permisos_as_admin(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """ADMIN puede ver los permisos de un rol."""
    from sqlalchemy import select
    from app.models.rol import Rol

    _user, token = await _make_user_with_rol(db_session, tenant, "admin_rp", "ADMIN")

    # Obtener el ID del rol ALUMNO
    result = await db_session.execute(select(Rol).where(Rol.code == "ALUMNO"))
    alumno = result.scalar_one()

    resp = await async_client.get(
        f"/api/v1/rbac/roles/{alumno.id}/permisos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    permisos = resp.json()
    assert isinstance(permisos, list)
    assert len(permisos) == 3, f"ALUMNO tiene 3 permisos, obtenido: {len(permisos)}"
    perm_codes = {p["permiso"]["code"] for p in permisos}
    assert "academico:ver_propio" in perm_codes
    assert "evaluacion:reservar" in perm_codes
    assert "avisos:confirmar" in perm_codes


@pytest.mark.asyncio
async def test_get_rol_permisos_without_permission_returns_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Sin permiso roles:ver → 403 en el endpoint de permisos del rol."""
    from sqlalchemy import select
    from app.models.rol import Rol

    _user, token = await _make_user_with_rol(db_session, tenant, "alumno_rp", "ALUMNO")

    result = await db_session.execute(select(Rol).where(Rol.code == "ALUMNO"))
    alumno = result.scalar_one()

    resp = await async_client.get(
        f"/api/v1/rbac/roles/{alumno.id}/permisos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403, f"Esperado 403, obtenido {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test — Endpoints existentes no se ven afectados
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_still_works(async_client: AsyncClient):
    """El endpoint /api/v1/health sigue respondiendo tras agregar RBAC router."""
    resp = await async_client.get("/health")
    assert resp.status_code == 200
