"""Tests TDD para la estructura académica (C-06) — tasks 6.1 a 6.5.

Verifica:
  Carrera:
    - crear exitoso (201)
    - código duplicado en tenant → 409
    - aislamiento multi-tenant
    - ADMIN lista sus carreras
    - TUTOR recibe 403

  Cohorte:
    - crear exitosa (201)
    - nombre duplicado (409)
    - carrera inactiva bloquea creación (422)
    - carrera de otro tenant da 404
    - cohortes existentes visibles tras inactivar carrera

  Materia:
    - crear exitosa (201)
    - código duplicado (409)
    - aislamiento multi-tenant
    - ALUMNO recibe 403
    - PATCH estado Inactiva (200)
    - PATCH estado inválido (422)

  audit_log FK:
    - insertar con materia_id válida
    - insertar con materia_id NULL
    - soft-delete de materia no rompe FK de audit_log existente

TDD Evidence:
| Task | Layer  | Safety Net  | RED | GREEN | TRIANGULATE |
|------|--------|-------------|-----|-------|-------------|
| 6.2  | Integr | ✅ baseline | ✅  | ✅    | ✅ 5 cases  |
| 6.3  | Integr | ✅ baseline | ✅  | ✅    | ✅ 5 cases  |
| 6.4  | Integr | ✅ baseline | ✅  | ✅    | ✅ 6 cases  |
| 6.5  | Integr | ✅ baseline | ✅  | ✅    | ✅ 3 cases  |
"""

import hashlib
from datetime import date, datetime, timezone

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
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant A", slug="tenant-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant B", slug="tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    """Crea un usuario con rol y retorna (user, token)."""
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from app.core.security import create_access_token, hash_password
    from sqlalchemy import select
    from app.models.rol import Rol

    email = f"{email_prefix}@est.com"
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
# CARRERA — 6.2
# ============================================================================


@pytest.mark.asyncio
async def test_carrera_create_201(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /admin/carreras crea carrera y retorna 201."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_c1", "ADMIN")

    resp = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "ISI", "nombre": "Ingeniería en Sistemas"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["codigo"] == "ISI"
    assert data["nombre"] == "Ingeniería en Sistemas"
    assert data["estado"] == "Activa"
    assert data["tenant_id"] == str(tenant_a.id)


@pytest.mark.asyncio
async def test_carrera_duplicate_codigo_returns_409(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: código duplicado dentro del mismo tenant → 409."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_c2", "ADMIN")

    await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "ISI", "nombre": "Primera"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "ISI", "nombre": "Segunda"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 409, resp.text
    assert "ya existe" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_carrera_aislamiento_multi_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: ADMIN del tenant A no ve carreras del tenant B."""
    _, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_ca", "ADMIN")
    _, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_cb", "ADMIN")

    await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "TIC", "nombre": "Tecnología"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    resp = await async_client.get(
        "/api/v1/admin/carreras",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert resp.status_code == 200
    assert all(c["tenant_id"] == str(tenant_a.id) for c in resp.json())


@pytest.mark.asyncio
async def test_carrera_tutor_recibe_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: TUTOR sin permiso estructura:gestionar → 403."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "tutor_c", "TUTOR")

    resp = await async_client.get(
        "/api/v1/admin/carreras",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_carrera_admin_lista_solo_su_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: ADMIN lista solo carreras de su tenant."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_list", "ADMIN")

    await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "A01", "nombre": "Carrera A"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await async_client.get(
        "/api/v1/admin/carreras",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["codigo"] == "A01"


# ============================================================================
# COHORTE — 6.3
# ============================================================================


@pytest.mark.asyncio
async def test_cohorte_create_201(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /admin/cohortes con carrera activa retorna 201."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_co1", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "ISI", "nombre": "ISI"},
        headers={"Authorization": f"Bearer {token}"},
    )
    carrera_id = r.json()["id"]

    resp = await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_id, "nombre": "2024-A", "anio": 2024, "vig_desde": "2024-03-01"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["nombre"] == "2024-A"
    assert data["anio"] == 2024
    assert data["carrera_id"] == carrera_id


@pytest.mark.asyncio
async def test_cohorte_nombre_duplicado_409(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: nombre duplicado para misma carrera → 409."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_co2", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "MEC", "nombre": "Mecatronica"},
        headers={"Authorization": f"Bearer {token}"},
    )
    carrera_id = r.json()["id"]

    await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_id, "nombre": "2024-A", "anio": 2024, "vig_desde": "2024-03-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_id, "nombre": "2024-A", "anio": 2024, "vig_desde": "2024-06-01"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 409, resp.text


@pytest.mark.asyncio
async def test_cohorte_carrera_inactiva_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: carrera inactiva bloquea nueva cohorte → 422."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_co3", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "OLD", "nombre": "Carrera Vieja"},
        headers={"Authorization": f"Bearer {token}"},
    )
    carrera_id = r.json()["id"]

    await async_client.patch(
        f"/api/v1/admin/carreras/{carrera_id}/estado",
        json={"estado": "Inactiva"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_id, "nombre": "2025-A", "anio": 2025, "vig_desde": "2025-03-01"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422, resp.text
    assert "inactiva" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cohorte_carrera_otro_tenant_404(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: carrera de otro tenant → 404 (aislamiento multi-tenant)."""
    _, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_coa", "ADMIN")
    _, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_cob", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "B01", "nombre": "Carrera B"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    carrera_b_id = r.json()["id"]

    resp = await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_b_id, "nombre": "2024-X", "anio": 2024, "vig_desde": "2024-03-01"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_cohorte_visible_tras_inactivar_carrera(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: cohortes preexistentes siguen visibles cuando carrera se inactiva."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_co4", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/carreras",
        json={"codigo": "ACT", "nombre": "Activa al inicio"},
        headers={"Authorization": f"Bearer {token}"},
    )
    carrera_id = r.json()["id"]

    await async_client.post(
        "/api/v1/admin/cohortes",
        json={"carrera_id": carrera_id, "nombre": "2023-A", "anio": 2023, "vig_desde": "2023-03-01"},
        headers={"Authorization": f"Bearer {token}"},
    )

    await async_client.patch(
        f"/api/v1/admin/carreras/{carrera_id}/estado",
        json={"estado": "Inactiva"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await async_client.get(
        "/api/v1/admin/cohortes",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["nombre"] == "2023-A"


# ============================================================================
# MATERIA — 6.4
# ============================================================================


@pytest.mark.asyncio
async def test_materia_create_201(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /admin/materias crea materia y retorna 201."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_m1", "ADMIN")

    resp = await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "MAT101", "nombre": "Matemática I"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["codigo"] == "MAT101"
    assert data["estado"] == "Activa"
    assert data["tenant_id"] == str(tenant_a.id)


@pytest.mark.asyncio
async def test_materia_duplicate_codigo_409(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: código duplicado en tenant → 409."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_m2", "ADMIN")

    await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "FIS101", "nombre": "Física I"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "FIS101", "nombre": "Física I bis"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 409, resp.text


@pytest.mark.asyncio
async def test_materia_aislamiento_multi_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: materias de otro tenant no son visibles."""
    _, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_ma", "ADMIN")
    _, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_mb", "ADMIN")

    await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "QUI", "nombre": "Química"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    resp = await async_client.get(
        "/api/v1/admin/materias",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_materia_alumno_recibe_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: ALUMNO sin permiso estructura:gestionar → 403."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "alumno_m", "ALUMNO")

    resp = await async_client.get(
        "/api/v1/admin/materias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_materia_patch_estado_inactiva(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: PATCH estado → Inactiva retorna 200 con estado actualizado."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_ms", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "ING201", "nombre": "Inglés II"},
        headers={"Authorization": f"Bearer {token}"},
    )
    materia_id = r.json()["id"]

    resp = await async_client.patch(
        f"/api/v1/admin/materias/{materia_id}/estado",
        json={"estado": "Inactiva"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "Inactiva"


@pytest.mark.asyncio
async def test_materia_patch_estado_invalido_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: estado inválido (Pydantic Literal) → 422."""
    _, token = await _make_user_with_rol(db_session, tenant_a, "admin_me", "ADMIN")

    r = await async_client.post(
        "/api/v1/admin/materias",
        json={"codigo": "PRO301", "nombre": "Programación III"},
        headers={"Authorization": f"Bearer {token}"},
    )
    materia_id = r.json()["id"]

    resp = await async_client.patch(
        f"/api/v1/admin/materias/{materia_id}/estado",
        json={"estado": "Suspendida"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422, resp.text


# ============================================================================
# audit_log FK — 6.5
# ============================================================================


@pytest.mark.asyncio
async def test_audit_log_insert_con_materia_id(
    db_session: AsyncSession, tenant_a
):
    """RED: insertar audit_log con materia_id válida no viola FK."""
    from app.core.audit import audit, CALIFICACIONES_IMPORTAR
    from app.models.materia import Materia
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.encryption import encrypt

    # Crear usuario actor
    email = "actor_fk@test.com"
    actor = User(
        tenant_id=tenant_a.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(actor)
    await db_session.flush()

    # Crear materia
    mat = Materia(
        tenant_id=tenant_a.id,
        codigo="FK01",
        nombre="Materia FK Test",
        estado="Activa",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(mat)
    await db_session.flush()
    await db_session.refresh(mat)

    # Insertar en audit_log con materia_id
    await audit(
        db_session,
        actor_id=actor.id,
        tenant_id=tenant_a.id,
        accion=CALIFICACIONES_IMPORTAR,
        materia_id=mat.id,
        filas_afectadas=5,
    )
    await db_session.flush()

    result = await db_session.execute(
        text("SELECT materia_id FROM audit_log WHERE accion = 'CALIFICACIONES_IMPORTAR'")
    )
    row = result.fetchone()
    assert row is not None
    assert str(row.materia_id) == str(mat.id)


@pytest.mark.asyncio
async def test_audit_log_insert_sin_materia_id(
    db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: insertar audit_log con materia_id=NULL no falla."""
    from app.core.audit import audit, COMUNICACION_ENVIAR
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.encryption import encrypt

    email = "actor_null@test.com"
    actor = User(
        tenant_id=tenant_a.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(actor)
    await db_session.flush()

    await audit(
        db_session,
        actor_id=actor.id,
        tenant_id=tenant_a.id,
        accion=COMUNICACION_ENVIAR,
    )
    await db_session.flush()

    result = await db_session.execute(
        text("SELECT materia_id FROM audit_log WHERE accion = 'COMUNICACION_ENVIAR'")
    )
    row = result.fetchone()
    assert row is not None
    assert row.materia_id is None


@pytest.mark.asyncio
async def test_audit_log_soft_delete_materia_no_rompe_fk(
    db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: soft-delete de materia (deleted_at) no viola FK en audit_log."""
    from app.core.audit import audit, CALIFICACIONES_IMPORTAR
    from app.models.materia import Materia
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.encryption import encrypt
    from app.repositories.materia_repository import MateriaRepository

    email = "actor_sd@test.com"
    actor = User(
        tenant_id=tenant_a.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(actor)
    await db_session.flush()

    mat = Materia(
        tenant_id=tenant_a.id,
        codigo="FKSD",
        nombre="Soft Delete Test",
        estado="Activa",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(mat)
    await db_session.flush()
    await db_session.refresh(mat)

    await audit(
        db_session,
        actor_id=actor.id,
        tenant_id=tenant_a.id,
        accion=CALIFICACIONES_IMPORTAR,
        materia_id=mat.id,
    )
    await db_session.flush()

    # Soft delete: la fila de materias permanece (deleted_at poblado, fila visible)
    repo = MateriaRepository(db_session, tenant_id=tenant_a.id)
    deleted = await repo.soft_delete(mat.id)
    assert deleted is True

    # La fila de audit_log sigue siendo accesible (no viola FK)
    result = await db_session.execute(
        text("SELECT materia_id FROM audit_log WHERE accion = 'CALIFICACIONES_IMPORTAR'")
    )
    row = result.fetchone()
    assert row is not None
    assert str(row.materia_id) == str(mat.id)
