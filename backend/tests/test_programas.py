"""Tests TDD para el módulo de programas y fechas académicas (C-17).

TDD Cycle Evidence:
| Task | Test | Layer | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|-----|-------|-------------|----------|
| crear_programa | test_crear_programa | Integr | ✅ | ✅ | ✅ filtrar por materia | ✅ |
| crear_fecha | test_crear_fecha_academica | Integr | ✅ | ✅ | ✅ filtrar por periodo | ✅ |
| editar_fecha | test_editar_fecha | Integr | ✅ | ✅ | ✅ | ✅ |
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


async def _make_estructura(db_session, tenant, prefix):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.materia import Materia

    carrera = Carrera(tenant_id=tenant.id, nombre=f"Car {prefix}", codigo=f"CA-{prefix}")
    db_session.add(carrera)
    await db_session.flush()
    cohorte = Cohorte(tenant_id=tenant.id, nombre=f"Coh {prefix}", anio=2024, carrera_id=carrera.id, vig_desde=date.today())
    materia = Materia(tenant_id=tenant.id, nombre=f"Mat {prefix}", codigo=f"MA-{prefix}")
    db_session.add_all([cohorte, materia])
    await db_session.flush()
    await db_session.commit()
    return carrera, cohorte, materia


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
    t = Tenant(name="Programas Tenant", slug="prg-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Programas Tenant B", slug="prg-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# ProgramaMateria CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_programa_materia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD crea programa de materia → 201 con referencia_archivo."""
    _, token_coord = await _make_user(db_session, tenant, "coord_prg1", "COORDINADOR")
    carrera, cohorte, materia = await _make_estructura(db_session, tenant, "prg1")

    resp = await async_client.post(
        "/api/v1/programas",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Programa 2026",
            "referencia_archivo": "s3://bucket/programas/mat-prg1-2026.pdf",
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["titulo"] == "Programa 2026"
    assert "referencia_archivo" in data
    assert str(data["tenant_id"]) == str(tenant.id)


@pytest.mark.asyncio
async def test_listar_programas_filtrado_por_materia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: filtrar programas por materia_id devuelve solo los de esa materia."""
    _, token_coord = await _make_user(db_session, tenant, "coord_prg2", "COORDINADOR")
    carrera_a, cohorte_a, materia_a = await _make_estructura(db_session, tenant, "prg2a")
    carrera_b, cohorte_b, materia_b = await _make_estructura(db_session, tenant, "prg2b")

    for mat, car, coh, titulo in [
        (materia_a, carrera_a, cohorte_a, "Prog A"),
        (materia_b, carrera_b, cohorte_b, "Prog B"),
    ]:
        await async_client.post(
            "/api/v1/programas",
            json={
                "materia_id": str(mat.id),
                "carrera_id": str(car.id),
                "cohorte_id": str(coh.id),
                "titulo": titulo,
                "referencia_archivo": f"s3://bucket/{titulo}.pdf",
            },
            headers={"Authorization": f"Bearer {token_coord}"},
        )

    resp = await async_client.get(
        f"/api/v1/programas?materia_id={materia_a.id}",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200
    programas = resp.json()
    assert all(p["materia_id"] == str(materia_a.id) for p in programas)
    assert all(p["titulo"] == "Prog A" for p in programas)


# ---------------------------------------------------------------------------
# FechaAcademica CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_fecha_academica(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD crea fecha académica → 201 con tipo y numero."""
    _, token_coord = await _make_user(db_session, tenant, "coord_fa1", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "fa1")

    resp = await async_client.post(
        "/api/v1/fechas-academicas",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15",
            "titulo": "Primer Parcial",
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo"] == "Parcial"
    assert data["numero"] == 1
    assert data["periodo"] == "2026-1"
    assert str(data["tenant_id"]) == str(tenant.id)


@pytest.mark.asyncio
async def test_listar_fechas_filtrado_por_periodo(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: filtrar por periodo devuelve solo las fechas de ese cuatrimestre."""
    _, token_coord = await _make_user(db_session, tenant, "coord_fa2", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "fa2")

    base = {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "tipo": "Parcial",
        "numero": 1,
        "fecha": "2026-04-01",
        "titulo": "Parcial",
    }

    for periodo in ["2026-1", "2026-2"]:
        await async_client.post(
            "/api/v1/fechas-academicas",
            json={**base, "periodo": periodo, "titulo": f"Parcial {periodo}"},
            headers={"Authorization": f"Bearer {token_coord}"},
        )

    resp = await async_client.get(
        "/api/v1/fechas-academicas?periodo=2026-1",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200
    fechas = resp.json()
    assert all(f["periodo"] == "2026-1" for f in fechas)
    assert any("2026-1" in f["titulo"] for f in fechas)


@pytest.mark.asyncio
async def test_editar_fecha_academica(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: editar fecha y titulo de una fecha académica → devuelve campos actualizados."""
    _, token_coord = await _make_user(db_session, tenant, "coord_fa3", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "fa3")

    resp_create = await async_client.post(
        "/api/v1/fechas-academicas",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "TP",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-05-01",
            "titulo": "TP Inicial",
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    fecha_id = resp_create.json()["id"]

    resp_patch = await async_client.patch(
        f"/api/v1/fechas-academicas/{fecha_id}",
        json={"fecha": "2026-05-15", "titulo": "TP Actualizado"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_patch.status_code == 200, resp_patch.text
    data = resp_patch.json()
    assert data["fecha"] == "2026-05-15"
    assert data["titulo"] == "TP Actualizado"


@pytest.mark.asyncio
async def test_soft_delete_fecha_academica(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: fecha soft-deleted no aparece en listados."""
    _, token_coord = await _make_user(db_session, tenant, "coord_fa4", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "fa4")

    resp_create = await async_client.post(
        "/api/v1/fechas-academicas",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "Coloquio",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-06-01",
            "titulo": "Coloquio Final",
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    fecha_id = resp_create.json()["id"]

    # Soft delete
    resp_del = await async_client.delete(
        f"/api/v1/fechas-academicas/{fecha_id}",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_del.status_code == 204

    # Ya no aparece en el listado
    resp_list = await async_client.get(
        "/api/v1/fechas-academicas",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    ids = [f["id"] for f in resp_list.json()]
    assert fecha_id not in ids


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_programas(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """RED: programa del tenant A no visible para tenant B."""
    _, token_coord_a = await _make_user(db_session, tenant, "coord_prg3a", "COORDINADOR")
    _, token_coord_b = await _make_user(db_session, tenant_b, "coord_prg3b", "COORDINADOR")
    carrera, cohorte, materia = await _make_estructura(db_session, tenant, "prg3")

    resp = await async_client.post(
        "/api/v1/programas",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Programa privado A",
            "referencia_archivo": "s3://bucket/private.pdf",
        },
        headers={"Authorization": f"Bearer {token_coord_a}"},
    )
    programa_id = resp.json()["id"]

    resp_b = await async_client.get(
        "/api/v1/programas",
        headers={"Authorization": f"Bearer {token_coord_b}"},
    )
    ids = [p["id"] for p in resp_b.json()]
    assert programa_id not in ids


@pytest.mark.asyncio
async def test_tenant_isolation_fechas(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """TRIANGULATE: fecha del tenant A no visible para tenant B."""
    _, token_coord_a = await _make_user(db_session, tenant, "coord_fa5a", "COORDINADOR")
    _, token_coord_b = await _make_user(db_session, tenant_b, "coord_fa5b", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "fa5")

    resp = await async_client.post(
        "/api/v1/fechas-academicas",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-01",
            "titulo": "Fecha privada A",
        },
        headers={"Authorization": f"Bearer {token_coord_a}"},
    )
    fecha_id = resp.json()["id"]

    resp_b = await async_client.get(
        "/api/v1/fechas-academicas",
        headers={"Authorization": f"Bearer {token_coord_b}"},
    )
    ids = [f["id"] for f in resp_b.json()]
    assert fecha_id not in ids
