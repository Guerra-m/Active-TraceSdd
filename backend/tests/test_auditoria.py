"""Tests TDD para el panel de auditoría y métricas (C-19).

TDD Cycle Evidence:
| Task | Test | Layer | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|-----|-------|-------------|----------|
| list_filtrado | test_log_admin_ve_todo | Integr | ✅ | ✅ | ✅ filtro por accion | ✅ |
| limit_default | test_log_limite | Integr | ✅ | ✅ | ✅ | ✅ |
| coord_propio | test_coord_solo_ve_propio | Integr | ✅ | ✅ | ✅ | ✅ |
| metricas | test_metricas_acciones_por_dia | Integr | ✅ | ✅ | ✅ por_actor | ✅ |
| tenant_isolation | test_tenant_isolation | Integr | ✅ | ✅ | ✅ | ✅ |
"""

import hashlib
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user(db_session, tenant, email_prefix: str, rol_code: str):
    from app.core.encryption import encrypt
    from app.core.security import create_access_token, hash_password
    from app.models.rol import Rol
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from sqlalchemy import select

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
        tenant_id=tenant.id, user_id=u.id, rol_id=rol.id,
        valid_from=date.today(), valid_until=None,
    )
    db_session.add(ur)
    await db_session.flush()
    await db_session.commit()

    token = create_access_token(data={"sub": str(u.id), "tenant_id": str(tenant.id), "type": "access"})
    return u, token


async def _insert_log(db_session, tenant_id, actor_id, accion="CALIFICACIONES_IMPORTAR", materia_id=None):
    """Inserta una entrada de AuditLog directamente en la DB."""
    from app.models.audit_log import AuditLog
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        materia_id=materia_id,
        accion=accion,
        fecha_hora=datetime.now(timezone.utc),
        filas_afectadas=1,
        ip="127.0.0.1",
    )
    db_session.add(entry)
    await db_session.flush()
    await db_session.commit()
    return entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Audit Tenant", slug="aud-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Audit Tenant B", slug="aud-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# Log filtrado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_admin_ve_todas_acciones(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: ADMIN ve todos los registros del tenant en /auditoria."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud1a", "PROFESOR")
    user_b, _ = await _make_user(db_session, tenant, "prof_aud1b", "PROFESOR")
    _, token_admin = await _make_user(db_session, tenant, "admin_aud1", "ADMIN")

    await _insert_log(db_session, tenant.id, user_a.id, "CALIFICACIONES_IMPORTAR")
    await _insert_log(db_session, tenant.id, user_b.id, "COMUNICACION_ENVIAR")

    resp = await async_client.get(
        "/api/v1/auditoria",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200, resp.text
    entries = resp.json()
    actores = {e["actor_id"] for e in entries}
    assert str(user_a.id) in actores
    assert str(user_b.id) in actores


@pytest.mark.asyncio
async def test_log_filtrado_por_accion(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: filtro por accion devuelve solo registros con esa accion."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud2a", "PROFESOR")
    _, token_admin = await _make_user(db_session, tenant, "admin_aud2", "ADMIN")

    await _insert_log(db_session, tenant.id, user_a.id, "CALIFICACIONES_IMPORTAR")
    await _insert_log(db_session, tenant.id, user_a.id, "COMUNICACION_ENVIAR")

    resp = await async_client.get(
        "/api/v1/auditoria?accion=CALIFICACIONES_IMPORTAR",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert all(e["accion"] == "CALIFICACIONES_IMPORTAR" for e in entries)


@pytest.mark.asyncio
async def test_log_limite_configurable(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: limit=1 devuelve solo 1 registro aunque haya más."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud3a", "PROFESOR")
    _, token_admin = await _make_user(db_session, tenant, "admin_aud3", "ADMIN")

    for _ in range(3):
        await _insert_log(db_session, tenant.id, user_a.id, "TEST_ACTION")

    resp = await async_client.get(
        "/api/v1/auditoria?limit=1",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# COORDINADOR (propio)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coordinador_solo_ve_sus_acciones(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORDINADOR (is_own=True) solo ve sus propias entradas."""
    user_prof, _ = await _make_user(db_session, tenant, "prof_aud4a", "PROFESOR")
    user_coord, token_coord = await _make_user(db_session, tenant, "coord_aud4b", "COORDINADOR")

    await _insert_log(db_session, tenant.id, user_prof.id, "CALIFICACIONES_IMPORTAR")
    await _insert_log(db_session, tenant.id, user_coord.id, "CALIFICACIONES_IMPORTAR")

    resp = await async_client.get(
        "/api/v1/auditoria",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200
    entries = resp.json()
    # COORDINADOR solo ve los suyos
    actor_ids = {e["actor_id"] for e in entries}
    assert all(a == str(user_coord.id) for a in actor_ids), f"Vio entradas de otro: {actor_ids}"


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_metricas_acciones_por_dia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: /metricas/acciones_por_dia agrega correctamente."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud5a", "PROFESOR")
    _, token_admin = await _make_user(db_session, tenant, "admin_aud5", "ADMIN")

    for _ in range(3):
        await _insert_log(db_session, tenant.id, user_a.id, "CALIFICACIONES_IMPORTAR")

    resp = await async_client.get(
        "/api/v1/auditoria/metricas",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "acciones_por_dia" in data
    assert "por_actor" in data
    total_dia = sum(d["total"] for d in data["acciones_por_dia"])
    assert total_dia >= 3


@pytest.mark.asyncio
async def test_metricas_por_actor_materia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: por_actor agrupa correctamente por actor_id."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud6a", "PROFESOR")
    user_b, _ = await _make_user(db_session, tenant, "prof_aud6b", "PROFESOR")
    _, token_admin = await _make_user(db_session, tenant, "admin_aud6", "ADMIN")

    await _insert_log(db_session, tenant.id, user_a.id, "TEST_A")
    await _insert_log(db_session, tenant.id, user_a.id, "TEST_A")
    await _insert_log(db_session, tenant.id, user_b.id, "TEST_B")

    resp = await async_client.get(
        "/api/v1/auditoria/metricas",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    data = resp.json()
    por_actor = data["por_actor"]
    actor_ids = [p["actor_id"] for p in por_actor]
    assert str(user_a.id) in actor_ids
    assert str(user_b.id) in actor_ids
    entry_a = next(p for p in por_actor if p["actor_id"] == str(user_a.id))
    assert entry_a["total"] >= 2


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_log(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """RED: ADMIN del tenant B no ve los registros del tenant A."""
    user_a, _ = await _make_user(db_session, tenant, "prof_aud7a", "PROFESOR")
    _, token_admin_b = await _make_user(db_session, tenant_b, "admin_aud7b", "ADMIN")

    entry = await _insert_log(db_session, tenant.id, user_a.id, "CALIFICACIONES_IMPORTAR")

    resp = await async_client.get(
        "/api/v1/auditoria",
        headers={"Authorization": f"Bearer {token_admin_b}"},
    )
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert str(entry.id) not in ids
