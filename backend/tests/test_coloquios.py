"""Tests TDD para el módulo de coloquios y evaluaciones (C-14).

TDD Cycle Evidence:
| Task | Test | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|------------|-----|-------|-------------|----------|
| 8.1-8.3 | crear_convocatoria | Integr | N/A (nuevo) | ✅ | ✅ | ✅ tipo=Parcial | ✅ |
| 8.4-8.6 | reservar_turno / sin_cupo | Integr | N/A | ✅ | ✅ | ✅ 422 sin cupo | ✅ |
| 8.7-8.8 | importar_alumnos | Integr | N/A | ✅ | ✅ | ✅ idempotente | ✅ |
| 8.9-8.10 | metricas | Integr | N/A | ✅ | ✅ | ✅ varias convocatorias | ✅ |
| 8.11-8.12 | tenant_isolation | Integr | N/A | ✅ | ✅ | ✅ reserva tenant B no visible | ✅ |
| 8.13-8.14 | resultado | Integr | N/A | ✅ | ✅ | ✅ update nota_final | ✅ |
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
    """Crea usuario con rol. Retorna (user, token)."""
    from app.core.security import create_access_token, hash_password
    from app.models.rol import Rol
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol
    from sqlalchemy import select

    email = f"{email_prefix}@test.com"
    email_hash = hashlib.sha256(email.lower().strip().encode()).hexdigest()

    from app.core.encryption import encrypt
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


async def _make_evaluacion(db_session, tenant, materia_id, cohorte_id, *,
                            tipo="Coloquio", instancia="Coloquio Final",
                            dias=2, cupos=5):
    """Crea una Evaluacion directamente en DB y retorna la instancia."""
    from app.models.evaluacion import Evaluacion

    ev = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=tipo,
        instancia=instancia,
        dias_disponibles=dias,
        cupos_por_dia=cupos,
    )
    db_session.add(ev)
    await db_session.flush()
    await db_session.refresh(ev)
    await db_session.commit()
    return ev


async def _make_estructura(db_session, tenant, prefix):
    """Crea Carrera + Cohorte + Materia. Retorna (carrera, cohorte, materia)."""
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.materia import Materia

    carrera = Carrera(tenant_id=tenant.id, nombre=f"Carrera {prefix}", codigo=f"CAR-{prefix}")
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant.id, nombre=f"Cohorte {prefix}", anio=2024,
        carrera_id=carrera.id, vig_desde=date.today(),
    )
    materia = Materia(tenant_id=tenant.id, nombre=f"Materia {prefix}", codigo=f"MAT-{prefix}")
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
    t = Tenant(name="Coloquios Tenant", slug="col-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Coloquios Tenant B", slug="col-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# 8.1-8.3 — Crear convocatoria (RED→GREEN→TRIANGULATE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_convocatoria_coloquio(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD crea convocatoria de coloquio → 201 con campos correctos."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col1", "COORDINADOR")
    _, _, materia = await _make_estructura(db_session, tenant, "col1")

    from app.models.cohorte import Cohorte
    from sqlalchemy import select
    result = await db_session.execute(
        select(Cohorte).where(Cohorte.tenant_id == tenant.id).limit(1)
    )
    cohorte = result.scalar_one()

    resp = await async_client.post(
        "/api/v1/coloquios",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "Coloquio",
            "instancia": "Coloquio Final",
            "dias_disponibles": 3,
            "cupos_por_dia": 5,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo"] == "Coloquio"
    assert data["instancia"] == "Coloquio Final"
    assert data["dias_disponibles"] == 3
    assert data["cupos_por_dia"] == 5
    assert str(data["tenant_id"]) == str(tenant.id)


@pytest.mark.asyncio
async def test_crear_convocatoria_tipo_parcial(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: crear convocatoria de tipo Parcial también funciona."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col2", "COORDINADOR")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col2")

    resp = await async_client.post(
        "/api/v1/coloquios",
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "tipo": "Parcial",
            "instancia": "1er Parcial",
            "dias_disponibles": 1,
            "cupos_por_dia": 30,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo"] == "Parcial"
    assert data["instancia"] == "1er Parcial"


# ---------------------------------------------------------------------------
# 8.4-8.6 — Reservar turno y validación de cupo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alumno_reserva_turno_exitoso(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: ALUMNO reserva turno en convocatoria con cupo disponible → 201."""
    _, _, materia = await _make_estructura(db_session, tenant, "col3")
    from app.models.cohorte import Cohorte
    from sqlalchemy import select
    result = await db_session.execute(
        select(Cohorte).where(Cohorte.tenant_id == tenant.id).limit(1)
    )
    cohorte = result.scalar_one()

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id, dias=2, cupos=5)
    alumno, token_alumno = await _make_user(db_session, tenant, "alumno_col3", "ALUMNO")

    resp = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/reservas",
        json={"fecha_hora": "2026-06-20 10:00"},
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado"] == "Activa"
    assert str(data["alumno_id"]) == str(alumno.id)
    assert str(data["evaluacion_id"]) == str(ev.id)


@pytest.mark.asyncio
async def test_reservar_sin_cupo_retorna_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: reservar con cupo_total=1 ya ocupado → 422."""
    _, _, materia = await _make_estructura(db_session, tenant, "col4")
    from app.models.cohorte import Cohorte
    from sqlalchemy import select
    result = await db_session.execute(
        select(Cohorte).where(Cohorte.tenant_id == tenant.id).limit(1)
    )
    cohorte = result.scalar_one()

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id, dias=1, cupos=1)

    alumno_a, token_a = await _make_user(db_session, tenant, "alumno_col4a", "ALUMNO")
    alumno_b, token_b = await _make_user(db_session, tenant, "alumno_col4b", "ALUMNO")

    # Alumno A ocupa el único cupo
    resp_a = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/reservas",
        json={"fecha_hora": "2026-06-20 10:00"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 201

    # Alumno B intenta reservar → 422
    resp_b = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/reservas",
        json={"fecha_hora": "2026-06-20 10:00"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 422


# ---------------------------------------------------------------------------
# 8.7-8.8 — Importar alumnos (convocados)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_importar_alumnos_crea_convocados(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD importa alumnos → crea ResultadoEvaluacion stubs (convocados)."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col5", "COORDINADOR")
    alumno_a, _ = await _make_user(db_session, tenant, "alumno_col5a", "ALUMNO")
    alumno_b, _ = await _make_user(db_session, tenant, "alumno_col5b", "ALUMNO")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col5")

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id)

    resp = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/alumnos",
        json={"alumno_ids": [str(alumno_a.id), str(alumno_b.id)]},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["importados"] == 2
    assert data["total_enviados"] == 2


@pytest.mark.asyncio
async def test_importar_alumnos_idempotente(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: importar el mismo alumno dos veces no duplica el registro."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col6", "COORDINADOR")
    alumno, _ = await _make_user(db_session, tenant, "alumno_col6", "ALUMNO")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col6")

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id)

    # Primera importación
    await async_client.post(
        f"/api/v1/coloquios/{ev.id}/alumnos",
        json={"alumno_ids": [str(alumno.id)]},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    # Segunda importación del mismo alumno
    resp = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/alumnos",
        json={"alumno_ids": [str(alumno.id)]},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["importados"] == 0, "No debe duplicar registros ya existentes"
    assert data["total_enviados"] == 1


# ---------------------------------------------------------------------------
# 8.9-8.10 — Métricas del panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_metricas_con_convocados_y_reservas(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: métricas reflejan convocados e instancias correctamente."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col7", "COORDINADOR")
    alumno, token_alumno = await _make_user(db_session, tenant, "alumno_col7", "ALUMNO")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col7")

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id, dias=2, cupos=10)

    # Importar 1 alumno convocado
    await async_client.post(
        f"/api/v1/coloquios/{ev.id}/alumnos",
        json={"alumno_ids": [str(alumno.id)]},
        headers={"Authorization": f"Bearer {token_coord}"},
    )

    # Alumno reserva turno
    await async_client.post(
        f"/api/v1/coloquios/{ev.id}/reservas",
        json={"fecha_hora": "2026-06-20 10:00"},
        headers={"Authorization": f"Bearer {token_alumno}"},
    )

    resp = await async_client.get(
        "/api/v1/coloquios/metricas",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["instancias_activas"] >= 1
    assert data["total_convocados"] >= 1
    assert data["reservas_activas"] >= 1


@pytest.mark.asyncio
async def test_metricas_tenant_vacio(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: tenant sin convocatorias devuelve ceros en métricas."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col8", "COORDINADOR")

    resp = await async_client.get(
        "/api/v1/coloquios/metricas",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["instancias_activas"] == 0
    assert data["total_convocados"] == 0
    assert data["reservas_activas"] == 0
    assert data["notas_registradas"] == 0


# ---------------------------------------------------------------------------
# 8.11-8.12 — Tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_evaluaciones(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """RED: convocatoria del tenant A no visible para tenant B."""
    _, token_coord_a = await _make_user(db_session, tenant, "coord_cola", "COORDINADOR")
    _, token_coord_b = await _make_user(db_session, tenant_b, "coord_colb", "COORDINADOR")
    _, cohorte_a, materia_a = await _make_estructura(db_session, tenant, "cola")

    ev_a = await _make_evaluacion(db_session, tenant, materia_a.id, cohorte_a.id)

    resp = await async_client.get(
        "/api/v1/coloquios",
        headers={"Authorization": f"Bearer {token_coord_b}"},
    )
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert str(ev_a.id) not in ids, "Tenant B no debe ver evaluaciones de Tenant A"


@pytest.mark.asyncio
async def test_alumno_no_puede_reservar_evaluacion_de_otro_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """TRIANGULATE: ALUMNO del tenant B intenta reservar en evaluacion del tenant A → 404."""
    _, cohorte_a, materia_a = await _make_estructura(db_session, tenant, "colc")
    ev_a = await _make_evaluacion(db_session, tenant, materia_a.id, cohorte_a.id, dias=5, cupos=10)

    alumno_b, token_b = await _make_user(db_session, tenant_b, "alumno_colc", "ALUMNO")

    resp = await async_client.post(
        f"/api/v1/coloquios/{ev_a.id}/reservas",
        json={"fecha_hora": "2026-06-20 10:00"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8.13-8.14 — Registro de resultado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registrar_resultado_exitoso(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: COORD registra nota final de alumno → 201 con nota_final."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col9", "COORDINADOR")
    alumno, _ = await _make_user(db_session, tenant, "alumno_col9", "ALUMNO")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col9")

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id)

    resp = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/resultados",
        json={"alumno_id": str(alumno.id), "nota_final": "8"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["nota_final"] == "8"
    assert str(data["alumno_id"]) == str(alumno.id)


@pytest.mark.asyncio
async def test_actualizar_nota_final(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: registrar resultado dos veces actualiza la nota (upsert)."""
    _, token_coord = await _make_user(db_session, tenant, "coord_col10", "COORDINADOR")
    alumno, _ = await _make_user(db_session, tenant, "alumno_col10", "ALUMNO")
    _, cohorte, materia = await _make_estructura(db_session, tenant, "col10")

    ev = await _make_evaluacion(db_session, tenant, materia.id, cohorte.id)

    # Primera nota
    await async_client.post(
        f"/api/v1/coloquios/{ev.id}/resultados",
        json={"alumno_id": str(alumno.id), "nota_final": "6"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )

    # Actualizar nota
    resp = await async_client.post(
        f"/api/v1/coloquios/{ev.id}/resultados",
        json={"alumno_id": str(alumno.id), "nota_final": "9"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["nota_final"] == "9", "La nota debe haberse actualizado"

    # Verificar que solo hay 1 resultado (no duplicado)
    resp_list = await async_client.get(
        f"/api/v1/coloquios/{ev.id}/resultados",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_list.status_code == 200
    resultados = resp_list.json()
    alumno_resultados = [r for r in resultados if r["alumno_id"] == str(alumno.id)]
    assert len(alumno_resultados) == 1
