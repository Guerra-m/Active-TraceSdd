"""Tests TDD para el módulo de tareas internas (C-16).

TDD Cycle Evidence:
| Task | Test | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|------------|-----|-------|-------------|----------|
| crear tarea | test_crear_tarea | Integr | N/A | ✅ | ✅ | ✅ sin materia | ✅ |
| mis tareas | test_profesor_ve_solo_sus_tareas | Integr | N/A | ✅ | ✅ | ✅ coord ve todas | ✅ |
| transiciones | test_cambiar_estado_tarea | Integr | N/A | ✅ | ✅ | ✅ multi-transicion | ✅ |
| comentarios | test_agregar_comentario | Integr | N/A | ✅ | ✅ | ✅ hilo ordenado | ✅ |
| tenant isolation | test_tenant_isolation | Integr | N/A | ✅ | ✅ | ✅ | ✅ |
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
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tareas Tenant", slug="tar-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tareas Tenant B", slug="tar-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# Crear tarea
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_tarea_con_descripcion(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD crea tarea asignada a PROF → 201, estado Pendiente."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar1", "COORDINADOR")
    prof, token_prof = await _make_user(db_session, tenant, "prof_tar1", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(prof.id),
            "descripcion": "Revisar las entregas del cuatrimestre",
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado"] == "Pendiente"
    assert str(data["asignado_a"]) == str(prof.id)
    assert str(data["asignado_por"]) == str(coord.id)
    assert str(data["tenant_id"]) == str(tenant.id)


@pytest.mark.asyncio
async def test_crear_tarea_sin_materia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: tarea sin materia_id (institucional) también se crea."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar2", "COORDINADOR")
    prof, _ = await _make_user(db_session, tenant, "prof_tar2", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(prof.id),
            "descripcion": "Tarea institucional sin materia",
            "materia_id": None,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["materia_id"] is None


# ---------------------------------------------------------------------------
# Mis tareas vs. todas las tareas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profesor_ve_solo_sus_tareas(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: PROFESOR solo ve las tareas asignadas a él."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar3", "COORDINADOR")
    prof_a, token_a = await _make_user(db_session, tenant, "prof_tar3a", "PROFESOR")
    prof_b, token_b = await _make_user(db_session, tenant, "prof_tar3b", "PROFESOR")

    # COORD crea tarea para PROF A
    await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof_a.id), "descripcion": "Tarea de A"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )

    # PROF B consulta → debe ver 0 tareas (no ve las de A)
    resp = await async_client.get(
        "/api/v1/tareas",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    for t in resp.json():
        assert str(t["asignado_a"]) == str(prof_b.id), "PROF B no debe ver tareas de PROF A"


@pytest.mark.asyncio
async def test_coord_ve_todas_las_tareas_del_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: COORD ve todas las tareas del tenant, no solo las suyas."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar4", "COORDINADOR")
    prof, _ = await _make_user(db_session, tenant, "prof_tar4", "PROFESOR")

    # COORD crea tarea asignada a PROF
    resp_create = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof.id), "descripcion": "Tarea visible para coord"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    tarea_id = resp_create.json()["id"]

    # COORD lista → debe ver la tarea aunque no esté asignada a él
    resp = await async_client.get(
        "/api/v1/tareas",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    ids = [t["id"] for t in resp.json()]
    assert tarea_id in ids, "COORD debe ver todas las tareas del tenant"


# ---------------------------------------------------------------------------
# Transiciones de estado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cambiar_estado_tarea(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: PROF actualiza estado de su tarea a 'En progreso'."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar5", "COORDINADOR")
    prof, token_prof = await _make_user(db_session, tenant, "prof_tar5", "PROFESOR")

    resp_create = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof.id), "descripcion": "Tarea a actualizar"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    tarea_id = resp_create.json()["id"]

    resp_patch = await async_client.patch(
        f"/api/v1/tareas/{tarea_id}",
        json={"estado": "En progreso"},
        headers={"Authorization": f"Bearer {token_prof}"},
    )
    assert resp_patch.status_code == 200, resp_patch.text
    assert resp_patch.json()["estado"] == "En progreso"


@pytest.mark.asyncio
async def test_transicion_completa_pendiente_a_resuelta(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: transición completa Pendiente → En progreso → Resuelta."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar6", "COORDINADOR")
    prof, token_prof = await _make_user(db_session, tenant, "prof_tar6", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof.id), "descripcion": "Flujo completo"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    tarea_id = resp.json()["id"]

    for estado_esperado in ["En progreso", "Resuelta"]:
        r = await async_client.patch(
            f"/api/v1/tareas/{tarea_id}",
            json={"estado": estado_esperado},
            headers={"Authorization": f"Bearer {token_prof}"},
        )
        assert r.status_code == 200
        assert r.json()["estado"] == estado_esperado


# ---------------------------------------------------------------------------
# Comentarios en hilo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agregar_comentario_y_ver_hilo(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD agrega comentario a tarea → aparece en hilo."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar7", "COORDINADOR")
    prof, token_prof = await _make_user(db_session, tenant, "prof_tar7", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof.id), "descripcion": "Con comentarios"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    tarea_id = resp.json()["id"]

    # COORD agrega comentario
    resp_com = await async_client.post(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        json={"texto": "Por favor avanzar antes del viernes"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_com.status_code == 201, resp_com.text
    assert resp_com.json()["texto"] == "Por favor avanzar antes del viernes"

    # PROF lee el hilo
    resp_hilo = await async_client.get(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        headers={"Authorization": f"Bearer {token_prof}"},
    )
    assert resp_hilo.status_code == 200
    assert len(resp_hilo.json()) == 1
    assert resp_hilo.json()[0]["texto"] == "Por favor avanzar antes del viernes"


@pytest.mark.asyncio
async def test_hilo_comentarios_ordenado(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: múltiples comentarios aparecen en orden cronológico."""
    coord, token_coord = await _make_user(db_session, tenant, "coord_tar8", "COORDINADOR")
    prof, token_prof = await _make_user(db_session, tenant, "prof_tar8", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof.id), "descripcion": "Hilo ordenado"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    tarea_id = resp.json()["id"]

    textos = ["Primer comentario", "Segundo comentario", "Tercer comentario"]
    for texto in textos:
        await async_client.post(
            f"/api/v1/tareas/{tarea_id}/comentarios",
            json={"texto": texto},
            headers={"Authorization": f"Bearer {token_coord}"},
        )

    resp_hilo = await async_client.get(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        headers={"Authorization": f"Bearer {token_prof}"},
    )
    assert resp_hilo.status_code == 200
    hilo_textos = [c["texto"] for c in resp_hilo.json()]
    assert hilo_textos == textos, f"Hilo desordenado: {hilo_textos}"


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_tareas(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """RED: tarea del tenant A no visible para tenant B."""
    coord_a, token_coord_a = await _make_user(db_session, tenant, "coord_tar9a", "COORDINADOR")
    prof_a, _ = await _make_user(db_session, tenant, "prof_tar9a", "PROFESOR")
    coord_b, token_coord_b = await _make_user(db_session, tenant_b, "coord_tar9b", "COORDINADOR")

    # Crear tarea en tenant A
    resp = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof_a.id), "descripcion": "Tarea de tenant A"},
        headers={"Authorization": f"Bearer {token_coord_a}"},
    )
    tarea_id = resp.json()["id"]

    # Tenant B lista → no debe ver la tarea de A
    resp_b = await async_client.get(
        "/api/v1/tareas",
        headers={"Authorization": f"Bearer {token_coord_b}"},
    )
    assert resp_b.status_code == 200
    ids_b = [t["id"] for t in resp_b.json()]
    assert tarea_id not in ids_b


@pytest.mark.asyncio
async def test_tenant_isolation_detalle_tarea(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """TRIANGULATE: COORD de tenant B no puede ver detalle de tarea de tenant A."""
    coord_a, token_coord_a = await _make_user(db_session, tenant, "coord_tar10a", "COORDINADOR")
    prof_a, _ = await _make_user(db_session, tenant, "prof_tar10a", "PROFESOR")
    coord_b, token_coord_b = await _make_user(db_session, tenant_b, "coord_tar10b", "COORDINADOR")

    resp = await async_client.post(
        "/api/v1/tareas",
        json={"asignado_a": str(prof_a.id), "descripcion": "Tarea privada A"},
        headers={"Authorization": f"Bearer {token_coord_a}"},
    )
    tarea_id = resp.json()["id"]

    # Tenant B intenta ver el detalle → 404
    resp_b = await async_client.get(
        f"/api/v1/tareas/{tarea_id}",
        headers={"Authorization": f"Bearer {token_coord_b}"},
    )
    assert resp_b.status_code == 404
