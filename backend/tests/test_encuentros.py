"""Tests TDD para endpoints de encuentros sincrónicos (C-13).

Suite de integración contra DB real (regla #4 — no mocks de DB).
"""

import hashlib
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user_token(db_session: AsyncSession, tenant, email_prefix: str, rol_code: str):
    """Crea usuario con rol y retorna (user, token, asignacion_id)."""
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

    # Crear materia, carrera, cohorte para la asignación
    carrera = Carrera(tenant_id=tenant.id, nombre="Ing. Sistemas", codigo=f"IS-{email_prefix}")
    db_session.add(carrera)
    await db_session.flush()
    cohorte = Cohorte(
        tenant_id=tenant.id, nombre="2024", anio=2024,
        carrera_id=carrera.id, vig_desde=date.today(),
    )
    materia = Materia(tenant_id=tenant.id, nombre="Matemática", codigo=f"MAT-{email_prefix}")
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
    return u, token, asig, materia


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
    t = Tenant(name="Encuentros Tenant", slug="enc-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant B", slug="enc-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# 6.1 — Slot recurrente 4 semanas genera 4 instancias
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slot_recurrente_4_semanas_genera_4_instancias(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """POST /encuentros/slots con cant_semanas=4 crea 1 slot + 4 instancias."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc1", "TUTOR")

    payload = {
        "materia_id": str(materia.id),
        "titulo": "Clase 1",
        "hora": "18:00:00",
        "dia_semana": "Lunes",
        "fecha_inicio": "2024-03-04",
        "cant_semanas": 4,
    }
    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Esperado 201, obtenido {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["slot"] is not None
    instancias = data["instancias"]
    assert len(instancias) == 4
    fechas = [i["fecha"] for i in instancias]
    assert "2024-03-04" in fechas
    assert "2024-03-11" in fechas
    assert "2024-03-18" in fechas
    assert "2024-03-25" in fechas
    for inst in instancias:
        assert inst["estado"] == "Programado"


# ---------------------------------------------------------------------------
# 6.2 — cant_semanas > 52 → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cant_semanas_mayor_52_retorna_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """cant_semanas=53 debe ser rechazado con 422."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc2", "TUTOR")

    payload = {
        "materia_id": str(materia.id),
        "titulo": "Clase",
        "hora": "18:00:00",
        "dia_semana": "Lunes",
        "fecha_inicio": "2024-03-04",
        "cant_semanas": 53,
    }
    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, f"Esperado 422, obtenido {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 6.3 — Encuentro único: 0 slots, 1 instancia con slot_id=NULL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_encuentro_unico_crea_1_instancia_sin_slot(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Modo único crea 1 InstanciaEncuentro con slot_id=None."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc3", "TUTOR")

    payload = {
        "materia_id": str(materia.id),
        "titulo": "Clase extraordinaria",
        "hora": "10:00:00",
        "fecha_unica": "2024-03-15",
    }
    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Esperado 201, obtenido {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["slot"] is None
    assert len(data["instancias"]) == 1
    assert data["instancias"][0]["slot_id"] is None
    assert data["instancias"][0]["fecha"] == "2024-03-15"


# ---------------------------------------------------------------------------
# 6.4 — Payload con ambos modos → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payload_ambos_modos_retorna_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Payload con cant_semanas Y fecha_unica → 422 (modos excluyentes)."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc4", "TUTOR")

    payload = {
        "materia_id": str(materia.id),
        "titulo": "Clase",
        "hora": "18:00:00",
        "fecha_inicio": "2024-03-04",
        "cant_semanas": 4,
        "fecha_unica": "2024-03-15",
    }
    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, f"Esperado 422, obtenido {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 6.5 — PATCH instancia: solo esa instancia cambia (RN-14)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_instancia_solo_esa_instancia_cambia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """PATCH /encuentros/{id} modifica solo la instancia indicada (RN-14)."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc5", "TUTOR")

    # Crear slot recurrente 2 semanas → 2 instancias
    payload = {
        "materia_id": str(materia.id),
        "titulo": "Clase TDD",
        "hora": "18:00:00",
        "dia_semana": "Martes",
        "fecha_inicio": "2024-03-05",
        "cant_semanas": 2,
    }
    resp_post = await async_client.post(
        "/api/v1/encuentros/slots",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_post.status_code == 201
    instancias = resp_post.json()["instancias"]
    assert len(instancias) == 2

    id_primera = instancias[0]["id"]
    id_segunda = instancias[1]["id"]

    # PATCH solo la primera
    resp_patch = await async_client.patch(
        f"/api/v1/encuentros/{id_primera}",
        json={"estado": "Realizado", "video_url": "https://video.example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_patch.status_code == 200, f"PATCH falló: {resp_patch.text}"
    assert resp_patch.json()["estado"] == "Realizado"

    # La segunda no debe haber cambiado
    resp_get = await async_client.get(
        f"/api/v1/encuentros/{id_segunda}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["estado"] == "Programado"


# ---------------------------------------------------------------------------
# 6.6 — PATCH instancia de otro tenant → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_instancia_otro_tenant_retorna_404(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """PATCH de instancia de otro tenant devuelve 404 (tenant isolation)."""
    _, token_a, asig_a, materia_a = await _make_user_token(db_session, tenant, "tutor_enc6a", "TUTOR")
    _, token_b, asig_b, materia_b = await _make_user_token(db_session, tenant_b, "tutor_enc6b", "TUTOR")

    # Crear encuentro en tenant A
    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json={
            "materia_id": str(materia_a.id),
            "titulo": "Clase A",
            "hora": "09:00:00",
            "fecha_unica": "2024-04-01",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 201
    id_inst_a = resp.json()["instancias"][0]["id"]

    # Tenant B intenta editar instancia de Tenant A → 404
    resp_patch = await async_client.patch(
        f"/api/v1/encuentros/{id_inst_a}",
        json={"comentario": "intento cruzado"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_patch.status_code == 404, f"Esperado 404, obtenido {resp_patch.status_code}"


# ---------------------------------------------------------------------------
# 6.7 — GET /aula-virtual: HTML correcto, canceladas excluidas, orden ASC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aula_virtual_html_correcto_canceladas_excluidas_orden_asc(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """GET /encuentros/aula-virtual retorna HTML con instancias no canceladas, orden ASC."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_enc7", "TUTOR")

    # Crear slot recurrente 3 semanas (fechas: 2024-03-04, 2024-03-11, 2024-03-18)
    resp_post = await async_client.post(
        "/api/v1/encuentros/slots",
        json={
            "materia_id": str(materia.id),
            "titulo": "Clase HTML",
            "hora": "14:00:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2024-03-04",
            "cant_semanas": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_post.status_code == 201
    instancias = resp_post.json()["instancias"]

    # Cancelar la del medio
    await async_client.patch(
        f"/api/v1/encuentros/{instancias[1]['id']}",
        json={"estado": "Cancelado"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await async_client.get(
        f"/api/v1/encuentros/aula-virtual?materia_id={materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    html = resp.text
    assert "<ul>" in html
    # Solo 2 instancias visibles (la cancelada excluida)
    assert html.count("<li>") == 2
    # Orden ascendente: 2024-03-04 antes de 2024-03-18
    pos_04 = html.find("2024-03-04")
    pos_18 = html.find("2024-03-18")
    assert pos_04 < pos_18, "Las instancias no están en orden ascendente"
    # La cancelada no debe aparecer
    assert "2024-03-11" not in html


# ---------------------------------------------------------------------------
# 6.8 — GET /admin: COORD ve todos los encuentros del tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_coord_ve_todos_los_encuentros_del_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """GET /encuentros/admin: COORDINADOR ve encuentros de todos los docentes."""
    _, token_tutor, asig_t, materia = await _make_user_token(db_session, tenant, "tutor_enc8", "TUTOR")
    _, token_coord, asig_c, _ = await _make_user_token(db_session, tenant, "coord_enc8", "COORDINADOR")

    # Tutor crea 2 encuentros
    for i in range(2):
        await async_client.post(
            "/api/v1/encuentros/slots",
            json={
                "materia_id": str(materia.id),
                "titulo": f"Clase {i}",
                "hora": "10:00:00",
                "fecha_unica": f"2024-05-0{i+1}",
            },
            headers={"Authorization": f"Bearer {token_tutor}"},
        )

    resp = await async_client.get(
        "/api/v1/encuentros/admin",
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200, f"Esperado 200: {resp.text}"
    data = resp.json()
    assert len(data) >= 2


# ---------------------------------------------------------------------------
# 6.9 — GET /admin tenant isolation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 8.1 — Triangular: slot recurrente de 1 semana (caso mínimo) → 1 instancia
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slot_recurrente_1_semana_genera_1_instancia(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Triangulación: cant_semanas=1 genera exactamente 1 instancia."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_tri1", "TUTOR")

    resp = await async_client.post(
        "/api/v1/encuentros/slots",
        json={
            "materia_id": str(materia.id),
            "titulo": "Clase única recurrente",
            "hora": "10:00:00",
            "dia_semana": "Viernes",
            "fecha_inicio": "2024-04-05",
            "cant_semanas": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slot"] is not None
    assert len(data["instancias"]) == 1
    assert data["instancias"][0]["fecha"] == "2024-04-05"


# ---------------------------------------------------------------------------
# 8.2 — Triangular: GET /aula-virtual sin instancias → HTML vacío <ul></ul>
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aula_virtual_sin_instancias_retorna_ul_vacio(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """Triangulación: GET /aula-virtual sin instancias retorna <ul></ul>."""
    _, token, asig, materia = await _make_user_token(db_session, tenant, "tutor_tri2", "TUTOR")

    resp = await async_client.get(
        f"/api/v1/encuentros/aula-virtual?materia_id={materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.text.strip() == "<ul></ul>"


@pytest.mark.asyncio
async def test_admin_tenant_isolation(
    async_client: AsyncClient, db_session: AsyncSession, tenant, tenant_b
):
    """GET /encuentros/admin solo retorna instancias del tenant del JWT."""
    _, token_a, asig_a, mat_a = await _make_user_token(db_session, tenant, "coord_enc9a", "COORDINADOR")
    _, token_b, asig_b, mat_b = await _make_user_token(db_session, tenant_b, "coord_enc9b", "COORDINADOR")

    # Tenant A crea 1 encuentro
    await async_client.post(
        "/api/v1/encuentros/slots",
        json={
            "materia_id": str(mat_a.id),
            "titulo": "Solo Tenant A",
            "hora": "09:00:00",
            "fecha_unica": "2024-06-01",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Tenant B consulta admin → no debe ver el de Tenant A
    resp = await async_client.get(
        "/api/v1/encuentros/admin",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for inst in data:
        # Ninguna instancia debe pertenecer al tenant A
        assert inst.get("tenant_id") != str(tenant.id)
