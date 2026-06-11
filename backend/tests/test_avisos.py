"""Tests TDD para el módulo de avisos y acknowledgments (C-15).

TDD Cycle Evidence:
| Task | Test | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|------|-------|------------|-----|-------|-------------|----------|
| 6.1-6.2 | Global visible + PorRol visible solo a rol correcto | Integr | N/A | ✅ | ✅ | ✅ | ✅ |
| 6.3-6.4 | Fuera de vigencia oculto + dentro visible | Integr | N/A | ✅ | ✅ | ✅ | ✅ |
| 6.5-6.6 | Ack registra + aviso ack-eado no aparece | Integr | N/A | ✅ | ✅ | ✅ | ✅ |
| 6.7-6.8 | Orden prioridad + PorMateria scope | Integr | N/A | ✅ | ✅ | ✅ | ✅ |
"""

import hashlib
from datetime import date, datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _past(hours: int = 1) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()


def _future(hours: int = 1) -> str:
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.isoformat()


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


async def _make_user_con_asignacion(db_session, tenant, email_prefix: str, rol_code: str):
    """Crea usuario con asignacion a una materia+cohorte específica."""
    from app.models.asignacion import Asignacion
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.materia import Materia

    u, token = await _make_user(db_session, tenant, email_prefix, rol_code)

    carrera = Carrera(tenant_id=tenant.id, nombre=f"Car {email_prefix}", codigo=f"C-{email_prefix}")
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(tenant_id=tenant.id, nombre="2024", anio=2024, carrera_id=carrera.id, vig_desde=date.today())
    materia = Materia(tenant_id=tenant.id, nombre=f"Mat {email_prefix}", codigo=f"M-{email_prefix}")
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

    return u, token, materia, cohorte


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
    t = Tenant(name="Avisos Tenant", slug="av-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Avisos Tenant B", slug="av-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# 6.1-6.2 — Aviso Global visible a todos; PorRol solo al rol correcto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aviso_global_visible_a_todos(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: aviso Global creado por COORD es visible para ALUMNO, TUTOR y COORD."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av1", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av1", "ALUMNO")

    # Crear aviso Global vigente
    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso global de prueba",
            "cuerpo": "Cuerpo del aviso",
            "inicio_en": _past(2),
            "fin_en": _future(2),
            "orden": 1,
            "activo": True,
            "requiere_ack": False,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    # ALUMNO ve el aviso
    resp_alumno = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    assert resp_alumno.status_code == 200
    ids = [a["id"] for a in resp_alumno.json()]
    assert aviso_id in ids, "ALUMNO debe ver el aviso Global"


@pytest.mark.asyncio
async def test_aviso_por_rol_solo_visible_al_rol_destino(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: aviso PorRol=TUTOR no es visible para ALUMNO."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av2", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av2", "ALUMNO")
    _, token_tutor = await _make_user(db_session, tenant, "tutor_av2", "TUTOR")

    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "PorRol",
            "rol_destino": "TUTOR",
            "severidad": "Advertencia",
            "titulo": "Solo para tutores",
            "cuerpo": "Cuerpo",
            "inicio_en": _past(1),
            "fin_en": _future(1),
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    # ALUMNO NO ve el aviso
    resp_alumno = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    ids_alumno = [a["id"] for a in resp_alumno.json()]
    assert aviso_id not in ids_alumno, "ALUMNO no debe ver aviso PorRol=TUTOR"

    # TUTOR SÍ ve el aviso
    resp_tutor = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_tutor}"},
    )
    ids_tutor = [a["id"] for a in resp_tutor.json()]
    assert aviso_id in ids_tutor, "TUTOR debe ver aviso PorRol=TUTOR"


# ---------------------------------------------------------------------------
# 6.3-6.4 — Vigencia (RN-18)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aviso_fuera_de_vigencia_no_aparece(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: aviso cuyo fin_en ya pasó no aparece en la lista."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av3", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av3", "ALUMNO")

    # Aviso ya expirado (fin_en en el pasado)
    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso expirado",
            "cuerpo": "Cuerpo",
            "inicio_en": _past(5),
            "fin_en": _past(2),  # ya pasó
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    resp_list = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    ids = [a["id"] for a in resp_list.json()]
    assert aviso_id not in ids, "Aviso expirado no debe aparecer"


@pytest.mark.asyncio
async def test_aviso_sin_fin_en_siempre_vigente(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: aviso sin fin_en (vigencia indefinida) siempre aparece."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av4", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av4", "ALUMNO")

    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso permanente",
            "cuerpo": "Cuerpo",
            "inicio_en": _past(10),
            "fin_en": None,  # sin fin
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    resp_list = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    ids = [a["id"] for a in resp_list.json()]
    assert aviso_id in ids, "Aviso sin fin_en debe aparecer siempre"


# ---------------------------------------------------------------------------
# 6.5-6.6 — Ack registra y aviso ack-eado no aparece (RN-19)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ack_registra_confirmacion(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: usuario confirma aviso con requiere_ack=True → 201."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av5", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av5", "ALUMNO")

    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Crítico",
            "titulo": "Aviso crítico con ack",
            "cuerpo": "Debes confirmar",
            "inicio_en": _past(1),
            "fin_en": _future(1),
            "orden": 0,
            "activo": True,
            "requiere_ack": True,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    # Alumno confirma lectura
    resp_ack = await async_client.post(
        f"/api/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    assert resp_ack.status_code == 201, resp_ack.text
    data = resp_ack.json()
    assert "confirmado_at" in data

    # Stats del aviso muestra 1 ack
    resp_stats = await async_client.get(
        f"/api/v1/avisos/{aviso_id}/stats",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_stats.status_code == 200
    assert resp_stats.json()["total_acks"] == 1


@pytest.mark.asyncio
async def test_aviso_ack_eado_no_aparece_en_lista(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: aviso con requiere_ack=True ya confirmado no aparece en GET /avisos."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av6", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av6", "ALUMNO")

    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso con ack requerido",
            "cuerpo": "Contenido",
            "inicio_en": _past(1),
            "fin_en": _future(1),
            "orden": 0,
            "activo": True,
            "requiere_ack": True,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201
    aviso_id = resp.json()["id"]

    # Antes del ack: aparece en la lista
    resp_antes = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    assert aviso_id in [a["id"] for a in resp_antes.json()], "Debe aparecer antes del ack"

    # Confirmar ack
    await async_client.post(
        f"/api/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )

    # Después del ack: ya no aparece
    resp_despues = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    ids_despues = [a["id"] for a in resp_despues.json()]
    assert aviso_id not in ids_despues, "Aviso ack-eado no debe aparecer en la lista"


# ---------------------------------------------------------------------------
# 6.7 — Orden de prioridad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_avisos_ordenados_por_orden_asc(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: avisos se devuelven ordenados por 'orden' ASC."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av7", "COORDINADOR")
    _, token_alumno = await _make_user(db_session, tenant, "alumno_av7", "ALUMNO")

    base = {
        "alcance": "Global",
        "severidad": "Info",
        "cuerpo": "Cuerpo",
        "inicio_en": _past(1),
        "fin_en": _future(1),
        "activo": True,
        "requiere_ack": False,
    }

    # Crear avisos con orden 10, 5, 1 (esperamos recibir en orden 1,5,10)
    for orden, titulo in [(10, "Aviso C"), (5, "Aviso B"), (1, "Aviso A")]:
        await async_client.post(
            "/api/v1/avisos",
            json={**base, "orden": orden, "titulo": titulo},
            headers={"Authorization": f"Bearer {token_coord}"},
        )

    resp = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_alumno}"},
    )
    assert resp.status_code == 200
    titles = [a["titulo"] for a in resp.json() if a["titulo"] in ("Aviso A", "Aviso B", "Aviso C")]
    assert titles == ["Aviso A", "Aviso B", "Aviso C"], f"Orden incorrecto: {titles}"


# ---------------------------------------------------------------------------
# 6.8 — Aviso PorMateria: solo usuario con asignacion en esa materia lo ve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aviso_por_materia_solo_para_asignados(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: aviso PorMateria solo visible a usuarios con asignacion en esa materia."""
    _, token_coord = await _make_user(db_session, tenant, "coord_av8", "COORDINADOR")
    tutor_asig, token_tutor_asig, materia_tutor, _ = await _make_user_con_asignacion(
        db_session, tenant, "tutor_av8a", "TUTOR"
    )
    _, token_tutor_sin_asig = await _make_user(db_session, tenant, "tutor_av8b", "TUTOR")

    # Aviso PorMateria para la materia del tutor_asig
    resp = await async_client.post(
        "/api/v1/avisos",
        json={
            "alcance": "PorMateria",
            "materia_id": str(materia_tutor.id),
            "severidad": "Info",
            "titulo": "Aviso de materia específica",
            "cuerpo": "Solo para esta materia",
            "inicio_en": _past(1),
            "fin_en": _future(1),
            "orden": 0,
            "activo": True,
            "requiere_ack": False,
        },
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 201, resp.text
    aviso_id = resp.json()["id"]

    # Tutor con asignacion en esa materia: SÍ ve el aviso
    resp_con_asig = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_tutor_asig}"},
    )
    assert aviso_id in [a["id"] for a in resp_con_asig.json()], "Tutor con asignación debe ver el aviso"

    # Tutor sin asignacion en esa materia: NO ve el aviso
    resp_sin_asig = await async_client.get(
        "/api/v1/avisos",
        headers={"Authorization": f"Bearer {token_tutor_sin_asig}"},
    )
    assert aviso_id not in [a["id"] for a in resp_sin_asig.json()], "Tutor sin asignación no debe ver el aviso"
