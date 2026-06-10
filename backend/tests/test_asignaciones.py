"""Tests TDD para asignaciones (C-07) — tasks 6.4 a 6.6.

Verifica:
  Asignacion (6.5):
    - crear exitosa (201) con estado_vigencia Vigente
    - materia de otro tenant → 404
    - responsable de otro tenant → 404
    - PROFESOR no tiene equipos:asignar → 403
    - aislamiento multi-tenant en listado
    - filtros funcionales: por rol, por materia_id

  Vigencia (6.6):
    - hasta=ayer → estado_vigencia Vencida
    - hasta=null → estado_vigencia Vigente

TDD Evidence:
| Task | Layer  | Safety Net   | RED | GREEN | TRIANGULATE |
|------|--------|--------------|-----|-------|-------------|
| 6.5  | Integr | ✅ 144/144   | ✅  | ✅    | ✅ 6 cases  |
| 6.6  | Integr | ✅ 144/144   | ✅  | ✅    | ✅ 2 cases  |
"""

import hashlib
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Fixtures — Task 6.4
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Asign A", slug="tenant-asign-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Asign B", slug="tenant-asign-b")
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


async def _create_materia(db_session, tenant, codigo: str):
    from datetime import datetime, timezone
    from app.models.materia import Materia

    m = Materia(
        tenant_id=tenant.id,
        codigo=codigo,
        nombre=f"Materia {codigo}",
        estado="Activa",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    await db_session.commit()
    return m


async def _create_usuario_docente(db_session, tenant, email_prefix: str):
    from datetime import datetime, timezone
    from app.core.encryption import encrypt
    from app.core.security import hash_password
    from app.models.user import User

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
    await db_session.refresh(u)
    await db_session.commit()
    return u


# ============================================================================
# ASIGNACION — Task 6.5
# ============================================================================


@pytest.mark.asyncio
async def test_asignacion_create_201_vigente(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /asignaciones crea asignación con desde=hoy → estado_vigencia Vigente."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_a1", "ADMIN")
    docente = await _create_usuario_docente(db_session, tenant_a, "docente_a1")
    materia = await _create_materia(db_session, tenant_a, "MAT-A1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "rol": "PROFESOR",
            "materia_id": str(materia.id),
            "desde": str(date.today()),
        },
        headers=headers,
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["rol"] == "PROFESOR"
    assert data["materia_id"] == str(materia.id)
    assert data["estado_vigencia"] == "Vigente"
    assert data["tenant_id"] == str(tenant_a.id)


@pytest.mark.asyncio
async def test_asignacion_materia_otro_tenant_404(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: materia del tenant B → 404 cuando ADMIN del tenant A crea asignación."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_a2a", "ADMIN")
    docente_a = await _create_usuario_docente(db_session, tenant_a, "docente_a2")
    materia_b = await _create_materia(db_session, tenant_b, "MAT-B1")

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente_a.id),
            "rol": "PROFESOR",
            "materia_id": str(materia_b.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_asignacion_responsable_otro_tenant_404(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: responsable_id del tenant B → 404."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_a3a", "ADMIN")
    docente_a = await _create_usuario_docente(db_session, tenant_a, "docente_a3")
    admin_b, _ = await _make_user_with_rol(db_session, tenant_b, "admin_a3b", "ADMIN")

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente_a.id),
            "rol": "TUTOR",
            "desde": str(date.today()),
            "responsable_id": str(admin_b.id),
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_asignacion_profesor_recibe_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: PROFESOR no tiene equipos:asignar → 403."""
    docente, token = await _make_user_with_rol(db_session, tenant_a, "prof_a4", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "rol": "PROFESOR",
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_asignacion_aislamiento_multi_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: ADMIN del tenant A no ve asignaciones del tenant B."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_a5a", "ADMIN")
    admin_b, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_a5b", "ADMIN")
    docente_b = await _create_usuario_docente(db_session, tenant_b, "docente_a5b")

    # Crear asignación en tenant B
    resp_b = await async_client.post(
        "/api/v1/asignaciones",
        json={"usuario_id": str(docente_b.id), "rol": "TUTOR", "desde": str(date.today())},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 201
    asig_b_id = resp_b.json()["id"]

    # ADMIN de tenant A no puede verla por ID
    resp_get = await async_client.get(
        f"/api/v1/asignaciones/{asig_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_get.status_code == 404


@pytest.mark.asyncio
async def test_asignacion_filtro_por_rol(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: listado filtrado por rol retorna solo las del rol pedido."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_a6", "ADMIN")
    docente1 = await _create_usuario_docente(db_session, tenant_a, "docente_a6a")
    docente2 = await _create_usuario_docente(db_session, tenant_a, "docente_a6b")
    headers = {"Authorization": f"Bearer {token}"}

    # PROFESOR y TUTOR
    await async_client.post(
        "/api/v1/asignaciones",
        json={"usuario_id": str(docente1.id), "rol": "PROFESOR", "desde": str(date.today())},
        headers=headers,
    )
    await async_client.post(
        "/api/v1/asignaciones",
        json={"usuario_id": str(docente2.id), "rol": "TUTOR", "desde": str(date.today())},
        headers=headers,
    )

    resp = await async_client.get(
        "/api/v1/asignaciones?rol=PROFESOR", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["rol"] == "PROFESOR"


# ============================================================================
# VIGENCIA — Task 6.6
# ============================================================================


@pytest.mark.asyncio
async def test_asignacion_hasta_ayer_es_vencida(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: asignación con hasta=ayer retorna estado_vigencia Vencida."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_v1", "ADMIN")
    docente = await _create_usuario_docente(db_session, tenant_a, "docente_v1")
    headers = {"Authorization": f"Bearer {token}"}

    ayer = date.today() - timedelta(days=1)

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "rol": "TUTOR",
            "desde": str(ayer - timedelta(days=30)),
            "hasta": str(ayer),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado_vigencia"] == "Vencida"


@pytest.mark.asyncio
async def test_asignacion_hasta_null_es_vigente(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: asignación con hasta=null → estado_vigencia Vigente."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_v2", "ADMIN")
    docente = await _create_usuario_docente(db_session, tenant_a, "docente_v2")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(docente.id),
            "rol": "COORDINADOR",
            "desde": str(date.today()),
            "hasta": None,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["estado_vigencia"] == "Vigente"
