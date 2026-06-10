"""Tests TDD para análisis académico (C-11) — tasks 9.1-9.6.

Verifica:
  9.1 — atrasados detecta reprobados: alumno con nota < umbral aparece en lista
  9.2 — atrasados detecta faltantes: alumno sin calificación de alguna actividad → atrasado
  9.3 — alumno al día (todas aprobadas, sin faltantes) no aparece en atrasados
  9.4 — ranking excluye alumnos sin ninguna aprobada (RN-09)
  9.5 — ranking orden DESC por aprobadas, determinístico por apellidos
  9.6 — notas finales calcula promedio numérico correcto (F2.5)

TDD Evidence:
| Task | Layer  | Safety Net   | RED | GREEN | TRIANGULATE                  |
|------|--------|--------------|-----|-------|------------------------------|
| 9.1  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ reprobado presente        |
| 9.2  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ faltante detectado        |
| 9.3  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ total_atrasados=0         |
| 9.4  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ sin aprobadas excluido    |
| 9.5  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ 3 alumnos ordenados       |
| 9.6  | Integr | ✅ 172/172   | ✅  | ✅    | ✅ promedio 80.00            |
"""

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Analisis Tenant", slug="analisis-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str):
    from sqlalchemy import select

    from app.core.encryption import encrypt
    from app.core.security import create_access_token, hash_password
    from app.models.rol import Rol
    from app.models.user import User
    from app.models.usuario_rol import UsuarioRol

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
    from app.models.usuario_rol import UsuarioRol
    ur = UsuarioRol(
        tenant_id=tenant.id, user_id=u.id, rol_id=rol.id,
        valid_from=date.today(), valid_until=None,
    )
    db_session.add(ur)
    await db_session.flush()
    await db_session.commit()

    token = create_access_token(data={
        "sub": str(u.id), "tenant_id": str(tenant.id), "type": "access",
    })
    return u, token


async def _create_materia(db_session, tenant, codigo: str):
    from app.models.materia import Materia
    m = Materia(tenant_id=tenant.id, codigo=codigo, nombre=f"Materia {codigo}")
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    await db_session.commit()
    return m


async def _create_asignacion(db_session, tenant, usuario, materia):
    from app.models.asignacion import Asignacion
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol="PROFESOR",
        materia_id=materia.id,
        desde=date.today(),
    )
    db_session.add(a)
    await db_session.flush()
    await db_session.refresh(a)
    await db_session.commit()
    return a


async def _create_entrada_padron(db_session, tenant, usuario, materia, nombre: str, apellidos: str):
    """Crea la cadena Carrera→Cohorte→VersionPadron→EntradaPadron para un alumno."""
    from app.core.encryption import encrypt
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.entrada_padron import EntradaPadron
    from app.models.version_padron import VersionPadron

    # Carrera (one per test call with unique code)
    import uuid as uuid_mod
    slug = uuid_mod.uuid4().hex[:8]
    carrera = Carrera(tenant_id=tenant.id, codigo=f"CAR-{slug}", nombre="Carrera Test")
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre=f"Cohorte-{slug}",
        anio=2025,
        vig_desde=date.today(),
    )
    db_session.add(cohorte)
    await db_session.flush()

    vp = VersionPadron(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        cargado_por=usuario.id,
        cargado_at=datetime.now(timezone.utc),
        activa=True,
    )
    db_session.add(vp)
    await db_session.flush()

    email = f"{nombre.lower()}.{apellidos.lower()}@students.test"
    ep = EntradaPadron(
        tenant_id=tenant.id,
        version_id=vp.id,
        nombre=nombre,
        apellidos=apellidos,
        email_encrypted=encrypt(email),
    )
    db_session.add(ep)
    await db_session.flush()
    await db_session.refresh(ep)
    await db_session.commit()
    return ep


async def _create_calificacion(
    db_session,
    tenant,
    asignacion,
    materia,
    entrada_padron,
    actividad: str,
    nota: float | None,
    aprobado: bool,
):
    from app.models.calificacion import Calificacion
    c = Calificacion(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        entrada_padron_id=entrada_padron.id,
        actividad=actividad,
        nota_numerica=Decimal(str(nota)) if nota is not None else None,
        aprobado=aprobado,
        importado_at=datetime.now(timezone.utc),
    )
    db_session.add(c)
    await db_session.flush()
    await db_session.commit()
    return c


# ---------------------------------------------------------------------------
# Task 9.1 — atrasados detecta reprobados
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_atrasados_detecta_reprobados(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: alumno con nota < umbral (aprobado=False) aparece en atrasados."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a1", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A1")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    ep_a = await _create_entrada_padron(db_session, tenant, profesor, materia, "Juan", "Reprobado")
    ep_b = await _create_entrada_padron(db_session, tenant, profesor, materia, "Ana", "Aprobada")

    await _create_calificacion(db_session, tenant, asignacion, materia, ep_a, "TP1", 50.0, False)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_b, "TP1", 80.0, True)

    resp = await async_client.get(
        f"/api/v1/analisis/atrasados/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_atrasados"] == 1
    assert len(data["alumnos"]) == 1
    atrasado = data["alumnos"][0]
    assert atrasado["apellidos"] == "Reprobado"
    assert "TP1" in atrasado["reprobadas"]
    assert atrasado["faltantes"] == []


# ---------------------------------------------------------------------------
# Task 9.2 — atrasados detecta faltantes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_atrasados_detecta_faltantes(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """GREEN: alumno sin calificación en alguna actividad → detectado como faltante."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a2", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A2")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    ep_incompleto = await _create_entrada_padron(db_session, tenant, profesor, materia, "Pepe", "Faltante")
    ep_completo = await _create_entrada_padron(db_session, tenant, profesor, materia, "Maria", "Completa")

    # ep_incompleto: solo TP1 (le falta TP2)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_incompleto, "TP1", 75.0, True)
    # ep_completo: TP1 y TP2 aprobadas
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_completo, "TP1", 80.0, True)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_completo, "TP2", 90.0, True)

    resp = await async_client.get(
        f"/api/v1/analisis/atrasados/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_atrasados"] == 1
    atrasado = data["alumnos"][0]
    assert atrasado["apellidos"] == "Faltante"
    assert "TP2" in atrasado["faltantes"]
    assert atrasado["reprobadas"] == []


# ---------------------------------------------------------------------------
# Task 9.3 — alumno al día no aparece en atrasados
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_atrasados_alumno_al_dia_no_aparece(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: todos los alumnos con todas las actividades aprobadas → lista vacía."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a3", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A3")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    for i, (nombre, apellido) in enumerate([("Luis", "Verde"), ("Rosa", "Blanca")]):
        ep = await _create_entrada_padron(db_session, tenant, profesor, materia, nombre, apellido)
        await _create_calificacion(db_session, tenant, asignacion, materia, ep, "TP1", 85.0, True)

    resp = await async_client.get(
        f"/api/v1/analisis/atrasados/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_atrasados"] == 0
    assert data["alumnos"] == []


# ---------------------------------------------------------------------------
# Task 9.4 — ranking excluye alumnos sin aprobadas (RN-09)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ranking_excluye_sin_aprobadas(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: alumno con aprobadas=0 no aparece en el ranking (RN-09)."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a4", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A4")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    ep_con = await _create_entrada_padron(db_session, tenant, profesor, materia, "Con", "Aprobadas")
    ep_sin = await _create_entrada_padron(db_session, tenant, profesor, materia, "Sin", "Aprobadas")

    await _create_calificacion(db_session, tenant, asignacion, materia, ep_con, "TP1", 80.0, True)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_sin, "TP1", 40.0, False)

    resp = await async_client.get(
        f"/api/v1/analisis/ranking/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_alumnos"] == 1
    assert data["ranking"][0]["apellidos"] == "Aprobadas"
    assert data["ranking"][0]["aprobadas"] == 1
    # "Sin Aprobadas" excluido
    apellidos_en_ranking = [r["apellidos"] for r in data["ranking"]]
    assert "Sin" not in [r["nombre"] for r in data["ranking"]]


# ---------------------------------------------------------------------------
# Task 9.5 — ranking orden DESC por aprobadas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ranking_orden_desc(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: 3 alumnos con distinto número de aprobadas → orden DESC correcto."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a5", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A5")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    # Alumno A: 1 aprobada
    ep_a = await _create_entrada_padron(db_session, tenant, profesor, materia, "Alice", "Uno")
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_a, "TP1", 80.0, True)

    # Alumno B: 3 aprobadas
    ep_b = await _create_entrada_padron(db_session, tenant, profesor, materia, "Bob", "Tres")
    for act in ["TP1", "TP2", "TP3"]:
        await _create_calificacion(db_session, tenant, asignacion, materia, ep_b, act, 85.0, True)

    # Alumno C: 2 aprobadas
    ep_c = await _create_entrada_padron(db_session, tenant, profesor, materia, "Carol", "Dos")
    for act in ["TP1", "TP2"]:
        await _create_calificacion(db_session, tenant, asignacion, materia, ep_c, act, 75.0, True)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep_c, "TP3", 40.0, False)

    resp = await async_client.get(
        f"/api/v1/analisis/ranking/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_alumnos"] == 3
    ranking = data["ranking"]
    assert ranking[0]["aprobadas"] == 3  # Bob/Tres
    assert ranking[1]["aprobadas"] == 2  # Carol/Dos
    assert ranking[2]["aprobadas"] == 1  # Alice/Uno
    assert ranking[0]["posicion"] == 1
    assert ranking[2]["posicion"] == 3


# ---------------------------------------------------------------------------
# Task 9.6 — notas finales calcula promedio
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notas_finales_promedio(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: alumno con 2 actividades numéricas → promedio correcto."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_a6", "PROFESOR")
    materia = await _create_materia(db_session, tenant, "MAT-A6")
    asignacion = await _create_asignacion(db_session, tenant, profesor, materia)

    ep = await _create_entrada_padron(db_session, tenant, profesor, materia, "Test", "Promedio")

    await _create_calificacion(db_session, tenant, asignacion, materia, ep, "TP1", 70.0, True)
    await _create_calificacion(db_session, tenant, asignacion, materia, ep, "TP2", 90.0, True)

    resp = await async_client.get(
        f"/api/v1/analisis/notas-finales/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_alumnos"] == 1
    alumno = data["alumnos"][0]
    assert alumno["apellidos"] == "Promedio"
    assert Decimal(str(alumno["promedio_numerico"])) == Decimal("80.00")
    assert alumno["aprobadas"] == 2
    assert alumno["total"] == 2
