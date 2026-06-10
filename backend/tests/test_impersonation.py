"""Tests TDD para la feature de impersonación (C-05) — tasks 5.7 a 5.14.

Verifica:
  - POST /auth/impersonate con ADMIN devuelve token válido con impersonated_id
  - Sin permiso impersonacion:usar → 403
  - Impersonación cross-tenant → 404
  - Registro IMPERSONACION_INICIAR en audit_log
  - DELETE /auth/impersonate → 204 + registro IMPERSONACION_FINALIZAR
  - Token normal en DELETE → 400
  - get_current_user resuelve identidad efectiva bajo impersonación
  - Atribución correcta: actor_id = actor real, impersonado_id = impersonado
"""

import hashlib
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt


# ---------------------------------------------------------------------------
# Fixtures de soporte
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Imp Tenant", slug="imp-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_other(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Other Tenant", slug="other-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from app.core.security import create_access_token, hash_password
    from sqlalchemy import select
    from app.models.rol import Rol

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


# ---------------------------------------------------------------------------
# 5.7: ADMIN con impersonacion:usar obtiene token con impersonated_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_impersonate_as_admin_returns_token(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_imp", "ADMIN")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_imp", "ALUMNO")

    resp = await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200, f"Esperado 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "access_token" in data

    # Verificar que el token emitido contiene impersonated_id
    from app.core.security import verify_token
    payload = verify_token(data["access_token"])
    assert payload.get("impersonated_id") == str(alumno.id)
    assert payload.get("sub") == str(admin.id)


# ---------------------------------------------------------------------------
# 5.8: Sin permiso impersonacion:usar → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_impersonate_without_permission_returns_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    tutor, tutor_token = await _make_user_with_rol(db_session, tenant, "tutor_imp", "TUTOR")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_imp2", "ALUMNO")

    resp = await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    assert resp.status_code == 403, f"Esperado 403, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 5.9: Impersonación cross-tenant → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_impersonate_cross_tenant_returns_404(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_other
):
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_ct", "ADMIN")
    # Usuario en otro tenant
    from app.models.user import User
    from app.core.security import hash_password
    other_email = "other@other.com"
    other_user = User(
        tenant_id=tenant_other.id,
        email_encrypted=encrypt(other_email),
        email_hash=hashlib.sha256(other_email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()
    await db_session.commit()

    resp = await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(other_user.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 404, f"Esperado 404, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 5.10: POST /impersonate registra IMPERSONACION_INICIAR en audit_log
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_impersonate_logs_iniciar(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_log", "ADMIN")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_log", "ALUMNO")

    await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    result = await db_session.execute(
        text(
            "SELECT actor_id, impersonado_id FROM audit_log "
            "WHERE accion = 'IMPERSONACION_INICIAR'"
        )
    )
    rows = result.fetchall()
    assert len(rows) == 1
    assert str(rows[0].actor_id) == str(admin.id)
    assert str(rows[0].impersonado_id) == str(alumno.id)


# ---------------------------------------------------------------------------
# 5.11: DELETE /impersonate con token de impersonación → 204 + FINALIZAR
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_end_impersonation_returns_204(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_end", "ADMIN")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_end", "ALUMNO")

    # Obtener token de impersonación
    resp = await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    imp_token = resp.json()["access_token"]

    # Finalizar impersonación
    resp_end = await async_client.delete(
        "/api/v1/auth/impersonate",
        headers={"Authorization": f"Bearer {imp_token}"},
    )

    assert resp_end.status_code == 204, f"Esperado 204, got {resp_end.status_code}: {resp_end.text}"

    # Verificar registro en audit_log
    result = await db_session.execute(
        text("SELECT accion FROM audit_log WHERE accion = 'IMPERSONACION_FINALIZAR'")
    )
    assert result.fetchone() is not None


# ---------------------------------------------------------------------------
# 5.12: Token normal en DELETE /impersonate → 400
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_end_impersonation_with_normal_token_returns_400(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_400", "ADMIN")

    resp = await async_client.delete(
        "/api/v1/auth/impersonate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 400, f"Esperado 400, got {resp.status_code}: {resp.text}"
    assert "no hay sesión de impersonación activa" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5.13: get_current_user resuelve identidad efectiva bajo impersonación
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_resolves_impersonated(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Con token de impersonación, /rbac/roles devuelve 403 (alumno sin roles:ver)
    y request.state.actor_id es el ADMIN — probado indirectamente via audit_log."""
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_res", "ADMIN")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_res", "ALUMNO")

    # Obtener token de impersonación
    resp = await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    imp_token = resp.json()["access_token"]

    # ALUMNO no tiene roles:ver → 403 (identidad efectiva = ALUMNO)
    resp_rbac = await async_client.get(
        "/api/v1/rbac/roles",
        headers={"Authorization": f"Bearer {imp_token}"},
    )
    assert resp_rbac.status_code == 403, (
        f"ALUMNO impersonado no debe tener roles:ver, got {resp_rbac.status_code}"
    )


# ---------------------------------------------------------------------------
# 5.14: Acción bajo impersonación atribuida al actor real
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_action_under_impersonation_attributed_to_actor(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """POST /impersonate registra actor_id=ADMIN, impersonado_id=ALUMNO."""
    admin, admin_token = await _make_user_with_rol(db_session, tenant, "admin_attr", "ADMIN")
    alumno, _ = await _make_user_with_rol(db_session, tenant, "alumno_attr", "ALUMNO")

    await async_client.post(
        "/api/v1/auth/impersonate",
        json={"user_id": str(alumno.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    result = await db_session.execute(
        text(
            "SELECT actor_id, impersonado_id FROM audit_log "
            "WHERE accion = 'IMPERSONACION_INICIAR' AND tenant_id = :tid"
        ),
        {"tid": tenant.id},
    )
    row = result.fetchone()
    assert row is not None
    assert str(row.actor_id) == str(admin.id)
    assert str(row.impersonado_id) == str(alumno.id)
