"""Tests TDD para perfil propio y mensajería interna (C-20).

TDD Cycle Evidence:
| Task | Test | Layer | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|-----|-------|-------------|----------|
| get_perfil | test_get_perfil | Integr | ✅ | ✅ | ✅ CUIL solo lectura | ✅ |
| update_perfil | test_update_perfil | Integr | ✅ | ✅ | ✅ campos parciales | ✅ |
| crear_hilo | test_crear_hilo | Integr | ✅ | ✅ | ✅ lista del inbox | ✅ |
| responder_hilo | test_responder_hilo | Integr | ✅ | ✅ | ✅ orden ASC | ✅ |
| tercero_sin_acceso | test_tercero_403 | Integr | ✅ | ✅ | ✅ | ✅ |
| tenant_isolation | test_tenant_isolation | Integr | ✅ | ✅ | ✅ | ✅ |
"""

import hashlib
from datetime import date

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
    t = Tenant(name="Perfil Tenant", slug="prf-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Perfil Tenant B", slug="prf-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_perfil_propio(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: GET /perfil devuelve los datos del usuario autenticado."""
    user, token = await _make_user(db_session, tenant, "prof_prf1", "PROFESOR")

    resp = await async_client.get(
        "/api/v1/perfil",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert str(data["id"]) == str(user.id)
    assert str(data["tenant_id"]) == str(tenant.id)
    assert "cuil" in data   # CUIL presente (puede ser null) pero nunca ausente
    assert "facturador" in data


@pytest.mark.asyncio
async def test_cuil_solo_lectura_en_put(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: CUIL no se puede cambiar vía PUT /perfil (extra='forbid')."""
    _, token = await _make_user(db_session, tenant, "prof_prf2", "PROFESOR")

    resp = await async_client.put(
        "/api/v1/perfil",
        json={"cuil": "20-12345678-0"},  # campo no declarado → 422
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_update_perfil_campos_editables(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: PUT /perfil actualiza nombre y banco; devuelve campos actualizados."""
    _, token = await _make_user(db_session, tenant, "prof_prf3", "PROFESOR")

    resp = await async_client.put(
        "/api/v1/perfil",
        json={"nombre": "Juan", "banco": "Galicia"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["nombre"] == "Juan"
    assert data["banco"] == "Galicia"


@pytest.mark.asyncio
async def test_update_perfil_parcial(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: PUT /perfil solo actualiza los campos enviados."""
    _, token = await _make_user(db_session, tenant, "prof_prf4", "PROFESOR")

    # Primera actualización
    await async_client.put(
        "/api/v1/perfil",
        json={"nombre": "Ana", "regional": "NOA"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Segunda actualización — solo banco
    resp2 = await async_client.put(
        "/api/v1/perfil",
        json={"banco": "Nacion"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp2.json()
    assert data["nombre"] == "Ana"   # no se pisó
    assert data["regional"] == "NOA"  # no se pisó
    assert data["banco"] == "Nacion"


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_hilo_inbox(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: POST /inbox crea hilo con primer mensaje → 201."""
    user_a, token_a = await _make_user(db_session, tenant, "prof_inb1a", "PROFESOR")
    user_b, token_b = await _make_user(db_session, tenant, "prof_inb1b", "COORDINADOR")

    resp = await async_client.post(
        "/api/v1/inbox",
        json={
            "destinatario_id": str(user_b.id),
            "asunto": "Consulta urgente",
            "primer_mensaje": "Hola, necesito hablar.",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["asunto"] == "Consulta urgente"
    assert str(data["remitente_id"]) == str(user_a.id)
    assert str(data["destinatario_id"]) == str(user_b.id)


@pytest.mark.asyncio
async def test_inbox_lista_hilos_propios(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: GET /inbox muestra solo hilos donde el usuario participa."""
    user_a, token_a = await _make_user(db_session, tenant, "prof_inb2a", "PROFESOR")
    user_b, token_b = await _make_user(db_session, tenant, "coord_inb2b", "COORDINADOR")
    user_c, token_c = await _make_user(db_session, tenant, "prof_inb2c", "PROFESOR")

    # Hilo A→B
    await async_client.post(
        "/api/v1/inbox",
        json={"destinatario_id": str(user_b.id), "asunto": "A a B", "primer_mensaje": "Msg1"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # Hilo C→B (no involucra a A)
    await async_client.post(
        "/api/v1/inbox",
        json={"destinatario_id": str(user_b.id), "asunto": "C a B", "primer_mensaje": "Msg2"},
        headers={"Authorization": f"Bearer {token_c}"},
    )

    resp_a = await async_client.get("/api/v1/inbox", headers={"Authorization": f"Bearer {token_a}"})
    hilos_a = resp_a.json()
    asuntos_a = [h["asunto"] for h in hilos_a]
    assert "A a B" in asuntos_a
    assert "C a B" not in asuntos_a  # A no participa en ese hilo


@pytest.mark.asyncio
async def test_responder_hilo_orden_asc(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: POST /inbox/{id} agrega mensaje; GET /{id} devuelve orden ASC."""
    user_a, token_a = await _make_user(db_session, tenant, "prof_inb3a", "PROFESOR")
    user_b, token_b = await _make_user(db_session, tenant, "coord_inb3b", "COORDINADOR")

    resp_hilo = await async_client.post(
        "/api/v1/inbox",
        json={"destinatario_id": str(user_b.id), "asunto": "Hilo orden", "primer_mensaje": "Primero"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    hilo_id = resp_hilo.json()["id"]

    # B responde
    await async_client.post(
        f"/api/v1/inbox/{hilo_id}",
        json={"cuerpo": "Segundo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # A lee el hilo
    resp_msgs = await async_client.get(
        f"/api/v1/inbox/{hilo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_msgs.status_code == 200
    msgs = resp_msgs.json()
    assert len(msgs) == 2
    assert msgs[0]["cuerpo"] == "Primero"
    assert msgs[1]["cuerpo"] == "Segundo"


@pytest.mark.asyncio
async def test_tercero_no_puede_ver_hilo(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: usuario que no es parte del hilo recibe 403."""
    user_a, token_a = await _make_user(db_session, tenant, "prof_inb4a", "PROFESOR")
    user_b, token_b = await _make_user(db_session, tenant, "coord_inb4b", "COORDINADOR")
    _, token_c = await _make_user(db_session, tenant, "prof_inb4c", "PROFESOR")

    resp_hilo = await async_client.post(
        "/api/v1/inbox",
        json={"destinatario_id": str(user_b.id), "asunto": "Privado", "primer_mensaje": "Solo entre nosotros"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    hilo_id = resp_hilo.json()["id"]

    resp_c = await async_client.get(
        f"/api/v1/inbox/{hilo_id}",
        headers={"Authorization": f"Bearer {token_c}"},
    )
    assert resp_c.status_code == 403


@pytest.mark.asyncio
async def test_tenant_isolation_inbox(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """RED: usuario de tenant B no ve los hilos de tenant A."""
    user_a, token_a = await _make_user(db_session, tenant, "prof_inb5a", "PROFESOR")
    user_b_same, _ = await _make_user(db_session, tenant, "coord_inb5b", "COORDINADOR")
    _, token_b_other = await _make_user(db_session, tenant_b, "coord_inb5c", "COORDINADOR")

    # Hilo en tenant A
    resp_hilo = await async_client.post(
        "/api/v1/inbox",
        json={"destinatario_id": str(user_b_same.id), "asunto": "Hilo A", "primer_mensaje": "Msg"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    hilo_id = resp_hilo.json()["id"]

    # Usuario de tenant B no lo ve en su lista
    resp_list = await async_client.get("/api/v1/inbox", headers={"Authorization": f"Bearer {token_b_other}"})
    ids = [h["id"] for h in resp_list.json()]
    assert hilo_id not in ids

    # Tampoco puede acceder directamente
    resp_direct = await async_client.get(
        f"/api/v1/inbox/{hilo_id}",
        headers={"Authorization": f"Bearer {token_b_other}"},
    )
    assert resp_direct.status_code == 404
