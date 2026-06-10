"""Tests para el guard require_permission (dependency FastAPI).

Suite TDD (Strict) para C-04 rbac-permisos-finos — tareas 8.6-8.8 y 8.11.
Verifica:
  - Usuario con permiso → endpoint responde 200
  - Usuario sin permiso → 403 con body correcto
  - Usuario no autenticado → 401 (guard de auth actúa antes)
  - request.state.permission_is_own_resource correcto para PROFESOR/COORDINADOR
  - Cache de request: una sola query a DB con múltiples require_permission
"""

import hashlib
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt


# ---------------------------------------------------------------------------
# Fixtures de test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    """Seed RBAC para todos los tests de este módulo."""
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant RBAC Guard Test", slug="tenant-rbac-guard")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user(db_session, tenant, email_prefix: str):
    from app.models.user import User
    from app.core.security import hash_password

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
    await db_session.refresh(u)
    return u


async def _get_rol(db_session, code: str):
    from sqlalchemy import select
    from app.models.rol import Rol
    result = await db_session.execute(select(Rol).where(Rol.code == code))
    return result.scalar_one()


async def _assign_rol(db_session, user, rol, tenant):
    from app.models.usuario_rol import UsuarioRol
    ur = UsuarioRol(
        tenant_id=tenant.id,
        user_id=user.id,
        rol_id=rol.id,
        valid_from=date.today(),
        valid_until=None,
    )
    db_session.add(ur)
    await db_session.flush()


async def _get_access_token(db_session, user, tenant) -> str:
    """Genera un access token válido para el usuario."""
    from app.core.security import create_access_token
    return create_access_token(data={
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "type": "access",
    })


# ---------------------------------------------------------------------------
# Registrar un router de prueba con require_permission
# ---------------------------------------------------------------------------


def _make_test_app_with_rbac_endpoint():
    """Crea una app FastAPI mínima con un endpoint protegido para tests."""
    from fastapi import FastAPI, Depends, Request
    from app.core.permissions import require_permission
    from app.core.dependencies import get_current_user

    app = FastAPI()

    @app.get("/test/protegido")
    async def endpoint_protegido(
        request: Request,
        _user=Depends(require_permission("avisos:confirmar")),
    ):
        return {
            "ok": True,
            "is_own_resource": getattr(request.state, "permission_is_own_resource", None),
        }

    @app.get("/test/propio")
    async def endpoint_propio(
        request: Request,
        _user=Depends(require_permission("calificaciones:importar")),
    ):
        return {
            "ok": True,
            "is_own_resource": getattr(request.state, "permission_is_own_resource", None),
        }

    @app.get("/test/doble-permiso")
    async def endpoint_doble(
        request: Request,
        _user1=Depends(require_permission("avisos:confirmar")),
        _user2=Depends(require_permission("avisos:confirmar")),
    ):
        return {"ok": True}

    return app


# ---------------------------------------------------------------------------
# Test 8.6 — Usuario CON permiso → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_with_permission_gets_200(
    db_session: AsyncSession, async_client: AsyncClient, tenant
):
    """Usuario con el permiso requerido accede al endpoint: responde 200."""
    from httpx import ASGITransport, AsyncClient as AClient

    user = await _make_user(db_session, tenant, "perm_ok")
    alumno = await _get_rol(db_session, "ALUMNO")
    await _assign_rol(db_session, user, alumno, tenant)
    await db_session.commit()

    token = await _get_access_token(db_session, user, tenant)
    app = _make_test_app_with_rbac_endpoint()

    async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get(
            "/test/protegido",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    assert resp.json()["ok"] is True


# ---------------------------------------------------------------------------
# Test 8.6 — Usuario SIN permiso → 403 con body correcto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_without_permission_gets_403(
    db_session: AsyncSession, async_client: AsyncClient, tenant
):
    """Usuario sin el permiso requerido recibe 403 con mensaje correcto."""
    from httpx import ASGITransport, AsyncClient as AClient

    # User sin ningún rol
    user = await _make_user(db_session, tenant, "no_perm")
    await db_session.commit()

    token = await _get_access_token(db_session, user, tenant)
    app = _make_test_app_with_rbac_endpoint()

    async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get(
            "/test/protegido",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 403, f"Esperado 403, obtenido {resp.status_code}: {resp.text}"
    detail = resp.json().get("detail", "")
    assert "Permiso insuficiente" in detail, f"Mensaje de error inesperado: {detail}"
    assert "avisos:confirmar" in detail, f"Permiso no mencionado en el error: {detail}"


# ---------------------------------------------------------------------------
# Test 8.7 — Usuario NO autenticado → 401 (auth guard actúa primero)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_user_gets_401(db_session: AsyncSession, tenant):
    """Petición sin Authorization → 401 antes de verificar permisos."""
    from httpx import ASGITransport, AsyncClient as AClient

    app = _make_test_app_with_rbac_endpoint()

    async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/test/protegido")  # sin header Authorization

    assert resp.status_code == 401, f"Esperado 401, obtenido {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test 8.8 — request.state.permission_is_own_resource
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profesor_calificaciones_is_own_resource_true(
    db_session: AsyncSession, tenant
):
    """PROFESOR accede a calificaciones:importar → is_own_resource=True."""
    from httpx import ASGITransport, AsyncClient as AClient

    user = await _make_user(db_session, tenant, "prof_state")
    profesor = await _get_rol(db_session, "PROFESOR")
    await _assign_rol(db_session, user, profesor, tenant)
    await db_session.commit()

    token = await _get_access_token(db_session, user, tenant)
    app = _make_test_app_with_rbac_endpoint()

    async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get(
            "/test/propio",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    assert resp.json()["is_own_resource"] is True


@pytest.mark.asyncio
async def test_coordinador_calificaciones_is_own_resource_false(
    db_session: AsyncSession, tenant
):
    """COORDINADOR accede a calificaciones:importar → is_own_resource=False."""
    from httpx import ASGITransport, AsyncClient as AClient

    user = await _make_user(db_session, tenant, "coord_state")
    coordinador = await _get_rol(db_session, "COORDINADOR")
    await _assign_rol(db_session, user, coordinador, tenant)
    await db_session.commit()

    token = await _get_access_token(db_session, user, tenant)
    app = _make_test_app_with_rbac_endpoint()

    async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get(
            "/test/propio",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    assert resp.json()["is_own_resource"] is False


# ---------------------------------------------------------------------------
# Test 8.11 — Cache de request: una sola query a DB con múltiples guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_cache_single_db_query(db_session: AsyncSession, tenant):
    """Dos require_permission en el mismo endpoint → una sola query a DB."""
    from httpx import ASGITransport, AsyncClient as AClient
    from unittest.mock import patch

    user = await _make_user(db_session, tenant, "cache_test")
    alumno = await _get_rol(db_session, "ALUMNO")
    await _assign_rol(db_session, user, alumno, tenant)
    await db_session.commit()

    token = await _get_access_token(db_session, user, tenant)
    app = _make_test_app_with_rbac_endpoint()

    call_count = 0

    from app.services import rbac_service as rbac_module
    original_fn = rbac_module.RbacService.get_effective_permissions

    async def spy_get_effective(user_id, tenant_id, db, reference_date=None):
        nonlocal call_count
        call_count += 1
        return await original_fn(
            user_id=user_id,
            tenant_id=tenant_id,
            db=db,
            reference_date=reference_date,
        )

    with patch.object(
        rbac_module.RbacService,
        "get_effective_permissions",
        staticmethod(spy_get_effective),
    ):
        async with AClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            resp = await client.get(
                "/test/doble-permiso",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert resp.status_code == 200, f"Esperado 200, obtenido {resp.status_code}: {resp.text}"
    assert call_count == 1, (
        f"get_effective_permissions debería llamarse 1 vez (cache), se llamó {call_count} veces"
    )
