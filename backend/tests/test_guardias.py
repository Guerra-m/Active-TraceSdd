"""Tests TDD para endpoints de guardias de atención (C-13).

Suite de integración contra DB real (regla #4 — no mocks de DB).
"""

import hashlib
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    """Crea usuario con rol y retorna (user, token, asig, materia, carrera, cohorte)."""
    from app.models.asignacion import Asignacion
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.materia import Materia
    from app.models.rol import Rol
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from app.core.security import create_access_token, hash_password
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

    carrera = Carrera(tenant_id=tenant.id, nombre="Ing. Informática", codigo=f"INF-{email_prefix}")
    db_session.add(carrera)
    await db_session.flush()
    cohorte = Cohorte(
        tenant_id=tenant.id, nombre="2024", anio=2024,
        carrera_id=carrera.id, vig_desde=date.today(),
    )
    materia = Materia(tenant_id=tenant.id, nombre="Redes", codigo=f"RED-{email_prefix}")
    db_session.add_all([cohorte, materia])
    await db_session.flush()

    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=u.id,
        rol=rol_code,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        desde=date.today(),
    )
    db_session.add(asig)
    await db_session.flush()
    await db_session.commit()

    token = create_access_token(data={
        "sub": str(u.id),
        "tenant_id": str(tenant.id),
        "type": "access",
    })
    return u, token, asig, materia, carrera, cohorte


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
    t = Tenant(name="Guardias Tenant", slug="grd-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Guardias Tenant B", slug="grd-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# 6.10 — POST guardia: creación exitosa con asignacion_id del JWT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_guardia_creacion_exitosa(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TUTOR crea guardia — asignacion_id se toma del JWT, no del payload."""
    _, token, asig, materia, carrera, cohorte = await _make_user_with_rol(
        db_session, tenant, "tutor_grd1", "TUTOR"
    )

    payload = {
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "dia": "Miércoles",
        "horario": "09:00-11:00",
        "estado": "Pendiente",
    }
    resp = await async_client.post(
        "/api/v1/guardias",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Esperado 201: {resp.text}"
    data = resp.json()
    assert data["estado"] == "Pendiente"
    assert data["dia"] == "Miércoles"
    assert str(data["tenant_id"]) == str(tenant.id)
    assert str(data["asignacion_id"]) == str(asig.id)


# ---------------------------------------------------------------------------
# 6.11 — GET guardias: TUTOR ve solo las suyas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tutor_ve_solo_sus_guardias(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TUTOR solo ve sus propias guardias, no las de otro tutor del mismo tenant."""
    _, token_a, asig_a, mat_a, car_a, coh_a = await _make_user_with_rol(
        db_session, tenant, "tutor_grd2a", "TUTOR"
    )
    _, token_b, asig_b, mat_b, car_b, coh_b = await _make_user_with_rol(
        db_session, tenant, "tutor_grd2b", "TUTOR"
    )

    # Tutor A crea una guardia
    await async_client.post(
        "/api/v1/guardias",
        json={
            "materia_id": str(mat_a.id),
            "carrera_id": str(car_a.id),
            "cohorte_id": str(coh_a.id),
            "dia": "Lunes",
            "horario": "08:00-10:00",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Tutor B consulta — debe ver 0 guardias (no ve la de A)
    resp = await async_client.get(
        "/api/v1/guardias",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for g in data:
        assert str(g["asignacion_id"]) == str(asig_b.id), "Tutor B no debe ver guardias de Tutor A"


# ---------------------------------------------------------------------------
# 6.12 — GET guardias: COORD ve todas las del tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coord_ve_todas_las_guardias_del_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """COORDINADOR puede ver todas las guardias del tenant."""
    _, token_t, asig_t, mat_t, car_t, coh_t = await _make_user_with_rol(
        db_session, tenant, "tutor_grd3", "TUTOR"
    )
    _, token_c, asig_c, mat_c, car_c, coh_c = await _make_user_with_rol(
        db_session, tenant, "coord_grd3", "COORDINADOR"
    )

    # Tutor crea guardia
    await async_client.post(
        "/api/v1/guardias",
        json={
            "materia_id": str(mat_t.id),
            "carrera_id": str(car_t.id),
            "cohorte_id": str(coh_t.id),
            "dia": "Viernes",
            "horario": "14:00-16:00",
        },
        headers={"Authorization": f"Bearer {token_t}"},
    )

    # COORD consulta → debe ver la guardia del tutor
    resp = await async_client.get(
        "/api/v1/guardias",
        headers={"Authorization": f"Bearer {token_c}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    asig_ids = [g["asignacion_id"] for g in data]
    assert str(asig_t.id) in asig_ids, "COORDINADOR debe ver guardias del tutor"


# ---------------------------------------------------------------------------
# 6.13 — GET /exportar: CSV con columnas correctas, tenant isolation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 8.3 — Triangular: TUTOR no puede ver guardias de otro TUTOR del mismo tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tutor_no_ve_guardias_de_otro_tutor_mismo_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Triangulación: TUTOR A no ve las guardias de TUTOR B (mismo tenant)."""
    _, token_a, asig_a, mat_a, car_a, coh_a = await _make_user_with_rol(
        db_session, tenant, "tutor_tri3a", "TUTOR"
    )
    _, token_b, asig_b, mat_b, car_b, coh_b = await _make_user_with_rol(
        db_session, tenant, "tutor_tri3b", "TUTOR"
    )

    # TUTOR A crea 2 guardias
    for dia in ["Lunes", "Martes"]:
        await async_client.post(
            "/api/v1/guardias",
            json={
                "materia_id": str(mat_a.id),
                "carrera_id": str(car_a.id),
                "cohorte_id": str(coh_a.id),
                "dia": dia,
                "horario": "08:00-10:00",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )

    # TUTOR B consulta → debe ver 0 (sus propias, que son ninguna)
    resp = await async_client.get(
        "/api/v1/guardias",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0, f"TUTOR B no debe ver guardias de TUTOR A, pero vio: {len(data)}"


@pytest.mark.asyncio
async def test_exportar_csv_columnas_correctas_y_tenant_isolation(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """GET /guardias/exportar devuelve CSV correcto y solo filas del tenant."""
    _, token_a, asig_a, mat_a, car_a, coh_a = await _make_user_with_rol(
        db_session, tenant, "coord_grd4a", "COORDINADOR"
    )
    _, token_b, asig_b, mat_b, car_b, coh_b = await _make_user_with_rol(
        db_session, tenant_b, "tutor_grd4b", "TUTOR"
    )

    # Cada tenant crea 1 guardia via su propio token
    await async_client.post(
        "/api/v1/guardias",
        json={
            "materia_id": str(mat_a.id),
            "carrera_id": str(car_a.id),
            "cohorte_id": str(coh_a.id),
            "dia": "Martes",
            "horario": "10:00-12:00",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    await async_client.post(
        "/api/v1/guardias",
        json={
            "materia_id": str(mat_b.id),
            "carrera_id": str(car_b.id),
            "cohorte_id": str(coh_b.id),
            "dia": "Jueves",
            "horario": "16:00-18:00",
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # Tenant A exporta — solo debe ver su guardia
    resp = await async_client.get(
        "/api/v1/guardias/exportar",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    lines = resp.text.strip().split("\n")
    # header + 1 fila (solo tenant A)
    assert len(lines) >= 2, "CSV debe tener header + al menos 1 fila"
    header = lines[0]
    assert "id" in header
    assert "asignacion_id" in header
    assert "dia" in header
    assert "horario" in header
    # Solo 1 fila de datos (el de tenant A)
    data_lines = [l for l in lines[1:] if l.strip()]
    assert len(data_lines) == 1, f"Tenant A debe ver solo 1 guardia, pero vio {len(data_lines)}"
