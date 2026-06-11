"""Tests TDD para equipos docentes (C-08).

Verifica:
  4.1  mis-equipos retorna solo asignaciones del JWT
  4.2  mis-equipos ignora query param usuario_id externo
  4.3  asignación masiva exitosa (1 y 3 usuarios)
  4.4  asignación masiva rechaza >200 usuarios
  4.5  asignación masiva rechaza usuario fuera de tenant
  4.6  clonado exitoso: solo vigentes se clonan
  4.7  clonado con conflictos: omite duplicados, retorna lista
  4.8  clonado rechaza origen == destino
  4.9  vigencia masiva actualiza N filas, ignora soft-deleted
  4.10 vigencia masiva sin campos retorna 422
  4.11 buscar-docentes con término válido
  4.12 buscar-docentes con término < 2 chars retorna 422
  4.13 export CSV: status 200, content-type text/csv, columnas correctas
  4.14 export tenant isolation

  7.1  triangular mis-equipos: tenant B no ve datos de tenant A
  7.2  triangular clonado: 0 asignaciones vigentes
  7.3  triangular masiva: rol viene del payload (no del contexto)
"""

import hashlib
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Fixtures compartidas
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Equipo A", slug="tenant-equipo-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant Equipo B", slug="tenant-equipo-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


async def _make_user_with_rol(db_session, tenant, email_prefix: str, rol_code: str, nombre: str = None, apellidos: str = None):
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
        nombre=nombre,
        apellidos=apellidos,
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


async def _create_carrera(db_session, tenant, codigo: str):
    from app.models.carrera import Carrera
    c = Carrera(tenant_id=tenant.id, codigo=codigo, nombre=f"Carrera {codigo}", estado="Activa")
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    await db_session.commit()
    return c


async def _create_cohorte(db_session, tenant, carrera, nombre: str):
    from datetime import date
    from app.models.cohorte import Cohorte
    c = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre=nombre,
        anio=2024,
        vig_desde=date(2024, 1, 1),
        vig_hasta=date(2024, 12, 31),
    )
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    await db_session.commit()
    return c


async def _create_materia(db_session, tenant, codigo: str):
    from app.models.materia import Materia
    m = Materia(tenant_id=tenant.id, codigo=codigo, nombre=f"Materia {codigo}", estado="Activa")
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    await db_session.commit()
    return m


async def _create_asignacion(db_session, tenant, usuario, materia, carrera, cohorte, rol="PROFESOR", desde=None, hasta=None, deleted=False):
    from app.models.asignacion import Asignacion
    from datetime import datetime, timezone
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol=rol,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        comisiones=[],
        desde=desde or date.today(),
        hasta=hasta,
    )
    if deleted:
        a.deleted_at = datetime.now(timezone.utc)
    db_session.add(a)
    await db_session.flush()
    await db_session.refresh(a)
    await db_session.commit()
    return a


# ---------------------------------------------------------------------------
# 4.1 — mis-equipos retorna solo asignaciones del JWT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mis_equipos_solo_jwt(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: GET /equipos/mis-equipos retorna solo las asignaciones del usuario autenticado."""
    coord, token = await _make_user_with_rol(db_session, tenant_a, "coord_me1", "COORDINADOR")
    otro, _ = await _make_user_with_rol(db_session, tenant_a, "otro_me1", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-ME1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-ME1")

    await _create_asignacion(db_session, tenant_a, coord, materia, carrera, cohorte)
    await _create_asignacion(db_session, tenant_a, otro, materia, carrera, cohorte)

    resp = await async_client.get(
        "/api/v1/equipos/mis-equipos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["usuario_id"] == str(coord.id)


# ---------------------------------------------------------------------------
# 4.2 — mis-equipos ignora query param usuario_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mis_equipos_ignora_usuario_id_param(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: mis-equipos ignora un usuario_id pasado como query param."""
    coord, token = await _make_user_with_rol(db_session, tenant_a, "coord_me2", "COORDINADOR")
    otro, _ = await _make_user_with_rol(db_session, tenant_a, "otro_me2", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-ME2")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-ME2")

    a_coord = await _create_asignacion(db_session, tenant_a, coord, materia, carrera, cohorte)
    await _create_asignacion(db_session, tenant_a, otro, materia, carrera, cohorte)

    resp = await async_client.get(
        f"/api/v1/equipos/mis-equipos?usuario_id={otro.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    ids = [d["usuario_id"] for d in resp.json()]
    assert str(coord.id) in ids
    assert str(otro.id) not in ids


# ---------------------------------------------------------------------------
# 4.3 — asignación masiva exitosa
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asignacion_masiva_1_usuario(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: POST /equipos/masiva con 1 usuario → 201, 1 asignación creada."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_mas1", "ADMIN")
    docente, _ = await _make_user_with_rol(db_session, tenant_a, "doc_mas1", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-MAS1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-MAS1")

    resp = await async_client.post(
        "/api/v1/equipos/masiva",
        json={
            "usuario_ids": [str(docente.id)],
            "rol": "PROFESOR",
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["creadas"] == 1


@pytest.mark.asyncio
async def test_asignacion_masiva_3_usuarios(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: asignación masiva con 3 usuarios → 3 asignaciones creadas."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_mas3", "ADMIN")
    docs = []
    for i in range(3):
        d, _ = await _make_user_with_rol(db_session, tenant_a, f"doc_mas3_{i}", "PROFESOR")
        docs.append(d)
    carrera = await _create_carrera(db_session, tenant_a, "CAR-MAS3")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-MAS3")

    resp = await async_client.post(
        "/api/v1/equipos/masiva",
        json={
            "usuario_ids": [str(d.id) for d in docs],
            "rol": "TUTOR",
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["creadas"] == 3


# ---------------------------------------------------------------------------
# 4.4 — masiva rechaza >200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asignacion_masiva_rechaza_mas_200(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: lista con 201 usuario_ids → 422."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_lim", "ADMIN")
    import uuid
    fake_ids = [str(uuid.uuid4()) for _ in range(201)]

    resp = await async_client.post(
        "/api/v1/equipos/masiva",
        json={
            "usuario_ids": fake_ids,
            "rol": "PROFESOR",
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4.5 — masiva rechaza usuario fuera de tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asignacion_masiva_usuario_otro_tenant(async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b):
    """RED: usuario de tenant_b en masiva de tenant_a → 404."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_mas_ta", "ADMIN")
    docente_b, _ = await _make_user_with_rol(db_session, tenant_b, "doc_mas_tb", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-OT1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-OT1")

    resp = await async_client.post(
        "/api/v1/equipos/masiva",
        json={
            "usuario_ids": [str(docente_b.id)],
            "rol": "PROFESOR",
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 4.6 — clonado exitoso: solo vigentes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clonar_solo_vigentes(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: clone_equipo duplica solo las asignaciones vigentes, no vencidas."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_cl1", "ADMIN")
    doc1, _ = await _make_user_with_rol(db_session, tenant_a, "doc_cl1a", "PROFESOR")
    doc2, _ = await _make_user_with_rol(db_session, tenant_a, "doc_cl1b", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-CL1")
    cohorte_orig = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    cohorte_dest = await _create_cohorte(db_session, tenant_a, carrera, "2024-2")
    materia = await _create_materia(db_session, tenant_a, "MAT-CL1")

    await _create_asignacion(db_session, tenant_a, doc1, materia, carrera, cohorte_orig)
    ayer = date.today() - timedelta(days=1)
    await _create_asignacion(db_session, tenant_a, doc2, materia, carrera, cohorte_orig, hasta=ayer)

    resp = await async_client.post(
        "/api/v1/equipos/clonar",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_origen_id": str(cohorte_orig.id),
            "cohorte_destino_id": str(cohorte_dest.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["creadas"] == 1
    assert data["conflictos"] == 0


# ---------------------------------------------------------------------------
# 4.7 — clonado con conflictos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clonar_con_conflictos(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: si ya existe asignación en destino, se omite y aparece en conflictos."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_cl2", "ADMIN")
    doc1, _ = await _make_user_with_rol(db_session, tenant_a, "doc_cl2a", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-CL2")
    cohorte_orig = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    cohorte_dest = await _create_cohorte(db_session, tenant_a, carrera, "2024-2")
    materia = await _create_materia(db_session, tenant_a, "MAT-CL2")

    await _create_asignacion(db_session, tenant_a, doc1, materia, carrera, cohorte_orig)
    await _create_asignacion(db_session, tenant_a, doc1, materia, carrera, cohorte_dest)

    resp = await async_client.post(
        "/api/v1/equipos/clonar",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_origen_id": str(cohorte_orig.id),
            "cohorte_destino_id": str(cohorte_dest.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["creadas"] == 0
    assert data["conflictos"] == 1


# ---------------------------------------------------------------------------
# 4.8 — clonado rechaza origen == destino
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clonar_rechaza_mismo_destino(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: cohorte_origen == cohorte_destino → 422."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_cl3", "ADMIN")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-CL3")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-CL3")

    resp = await async_client.post(
        "/api/v1/equipos/clonar",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_origen_id": str(cohorte.id),
            "cohorte_destino_id": str(cohorte.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4.9 — vigencia masiva actualiza N filas, ignora soft-deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vigencia_masiva_actualiza_activos(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: PATCH /equipos/vigencia actualiza solo asignaciones no eliminadas."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_vig1", "ADMIN")
    doc1, _ = await _make_user_with_rol(db_session, tenant_a, "doc_vig1a", "PROFESOR")
    doc2, _ = await _make_user_with_rol(db_session, tenant_a, "doc_vig1b", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-VIG1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-VIG1")

    await _create_asignacion(db_session, tenant_a, doc1, materia, carrera, cohorte)
    await _create_asignacion(db_session, tenant_a, doc2, materia, carrera, cohorte, deleted=True)

    nueva_hasta = str(date.today() + timedelta(days=90))
    resp = await async_client.patch(
        "/api/v1/equipos/vigencia",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "hasta": nueva_hasta,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["filas_actualizadas"] == 1


# ---------------------------------------------------------------------------
# 4.10 — vigencia masiva sin campos → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vigencia_masiva_sin_campos_422(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: PATCH vigencia sin desde ni hasta → 422."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_vig2", "ADMIN")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-VIG2")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-VIG2")

    resp = await async_client.patch(
        "/api/v1/equipos/vigencia",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4.11 — buscar-docentes con término válido
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buscar_docentes_termino_valido(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: GET /equipos/buscar-docentes?q=Mar retorna usuarios con nombre match."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_bsc1", "ADMIN",
                                             nombre="Admin", apellidos="System")
    doc, _ = await _make_user_with_rol(db_session, tenant_a, "doc_bsc1", "PROFESOR",
                                       nombre="María", apellidos="García")

    resp = await async_client.get(
        "/api/v1/equipos/buscar-docentes?q=Mar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    nombres = [d["nombre"] for d in resp.json()]
    assert "María" in nombres


# ---------------------------------------------------------------------------
# 4.12 — buscar-docentes < 2 chars → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buscar_docentes_termino_corto_422(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: q con 1 carácter → 422."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_bsc2", "ADMIN")

    resp = await async_client.get(
        "/api/v1/equipos/buscar-docentes?q=M",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4.13 — export CSV: 200, content-type, columnas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_csv_columnas(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """RED: GET /equipos/exportar retorna CSV con encabezados correctos."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_exp1", "ADMIN")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-EXP1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-EXP1")

    resp = await async_client.get(
        "/api/v1/equipos/exportar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")

    lines = resp.text.strip().split("\n")
    header = lines[0]
    assert "usuario_email" in header
    assert "rol" in header
    assert "estado_vigencia" in header


# ---------------------------------------------------------------------------
# 4.14 — export tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_tenant_isolation(async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b):
    """RED: el CSV de tenant A no incluye filas de tenant B."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_expi_a", "ADMIN")
    doc_a, _ = await _make_user_with_rol(db_session, tenant_a, "doc_expi_a", "PROFESOR")
    doc_b, _ = await _make_user_with_rol(db_session, tenant_b, "doc_expi_b", "PROFESOR")

    carrera_a = await _create_carrera(db_session, tenant_a, "CAR-EXPI-A")
    cohorte_a = await _create_cohorte(db_session, tenant_a, carrera_a, "2024-1")
    materia_a = await _create_materia(db_session, tenant_a, "MAT-EXPI-A")
    await _create_asignacion(db_session, tenant_a, doc_a, materia_a, carrera_a, cohorte_a)

    carrera_b = await _create_carrera(db_session, tenant_b, "CAR-EXPI-B")
    cohorte_b = await _create_cohorte(db_session, tenant_b, carrera_b, "2024-1")
    materia_b = await _create_materia(db_session, tenant_b, "MAT-EXPI-B")
    await _create_asignacion(db_session, tenant_b, doc_b, materia_b, carrera_b, cohorte_b)

    resp = await async_client.get(
        "/api/v1/equipos/exportar",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert len(lines) == 2  # encabezado + 1 fila del tenant A


# ---------------------------------------------------------------------------
# 7.1 — triangular: tenant B no ve datos de A
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mis_equipos_tenant_isolation(async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b):
    """TRIANGULATE: usuario de tenant B no ve asignaciones de tenant A."""
    coord_a, token_a = await _make_user_with_rol(db_session, tenant_a, "coord_ti_a", "COORDINADOR")
    coord_b, token_b = await _make_user_with_rol(db_session, tenant_b, "coord_ti_b", "COORDINADOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-TI")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-TI")
    await _create_asignacion(db_session, tenant_a, coord_a, materia, carrera, cohorte)

    resp = await async_client.get(
        "/api/v1/equipos/mis-equipos",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# 7.2 — triangular: clonado con 0 asignaciones vigentes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clonar_sin_vigentes(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """TRIANGULATE: clonar equipo sin asignaciones vigentes → 201, creadas=0."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_cl4", "ADMIN")
    doc, _ = await _make_user_with_rol(db_session, tenant_a, "doc_cl4", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-CL4")
    cohorte_orig = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    cohorte_dest = await _create_cohorte(db_session, tenant_a, carrera, "2024-2")
    materia = await _create_materia(db_session, tenant_a, "MAT-CL4")

    ayer = date.today() - timedelta(days=1)
    await _create_asignacion(db_session, tenant_a, doc, materia, carrera, cohorte_orig, hasta=ayer)

    resp = await async_client.post(
        "/api/v1/equipos/clonar",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_origen_id": str(cohorte_orig.id),
            "cohorte_destino_id": str(cohorte_dest.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["creadas"] == 0


# ---------------------------------------------------------------------------
# 7.3 — triangular masiva: rol viene del payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asignacion_masiva_rol_del_payload(async_client: AsyncClient, db_session: AsyncSession, tenant_a):
    """TRIANGULATE: el rol de la asignación masiva viene del payload, no del contexto del usuario."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_rol1", "ADMIN")
    doc, _ = await _make_user_with_rol(db_session, tenant_a, "doc_rol1", "PROFESOR")
    carrera = await _create_carrera(db_session, tenant_a, "CAR-ROL1")
    cohorte = await _create_cohorte(db_session, tenant_a, carrera, "2024-1")
    materia = await _create_materia(db_session, tenant_a, "MAT-ROL1")

    resp = await async_client.post(
        "/api/v1/equipos/masiva",
        json={
            "usuario_ids": [str(doc.id)],
            "rol": "TUTOR",
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "desde": str(date.today()),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    asignaciones = resp.json()["asignaciones"]
    assert asignaciones[0]["rol"] == "TUTOR"
