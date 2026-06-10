"""Tests TDD para padrón de alumnos (C-09) — tasks 8.1-8.6.

Verifica:
  8.1 — importar CSV válido → 201 con filas_importadas correcto
  8.2 — email_encrypted en DB no contiene el plaintext (cifrado AES-256-GCM)
  8.3 — segunda importación desactiva versión anterior (versionado D1)
  8.4 — PROFESOR sin asignación vigente en la materia → 403 (is_own_resource)
  8.5 — aislamiento multi-tenant: admin_b no accede a datos del padron de tenant_a
  8.6 — sync-moodle sin MOODLE_URL/TOKEN configurado → 422

TDD Evidence:
| Task | Layer  | Safety Net   | RED | GREEN | TRIANGULATE         |
|------|--------|--------------|-----|-------|---------------------|
| 8.1  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ 201 + fields ok  |
| 8.2  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ ciphertext check |
| 8.3  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ 2 versions       |
| 8.4  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ 403 on no-asign  |
| 8.5  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ tenant isolation |
| 8.6  | Integr | ✅ 160/160   | ✅  | ✅    | ✅ 422 from moodle  |
"""

import hashlib
import io
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Padron Tenant A", slug="padron-tenant-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Padron Tenant B", slug="padron-tenant-b")
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
    from app.models.materia import Materia

    m = Materia(
        tenant_id=tenant.id,
        codigo=codigo,
        nombre=f"Materia {codigo}",
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    await db_session.commit()
    return m


async def _create_cohorte(db_session, tenant, nombre: str):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte

    carrera = Carrera(
        tenant_id=tenant.id,
        codigo=f"CAR-{nombre[:6]}",
        nombre=f"Carrera {nombre}",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre=nombre,
        anio=2025,
        vig_desde=date.today(),
    )
    db_session.add(cohorte)
    await db_session.flush()
    await db_session.refresh(cohorte)
    await db_session.commit()
    return cohorte


def _csv_bytes(rows: list[dict]) -> bytes:
    """Genera un CSV en bytes para usar en upload."""
    lines = ["nombre,apellidos,email,comision,regional"]
    for r in rows:
        lines.append(
            f"{r['nombre']},{r['apellidos']},{r['email']},"
            f"{r.get('comision', '')},{r.get('regional', '')}"
        )
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# Task 8.1 — importar CSV válido → 201
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_importar_csv_201(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /padron/importar con CSV válido → 201 con filas_importadas=2."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_p1", "ADMIN")
    materia = await _create_materia(db_session, tenant_a, "MAT-P1")
    cohorte = await _create_cohorte(db_session, tenant_a, "2025-A")

    csv_data = _csv_bytes([
        {"nombre": "Juan", "apellidos": "Pérez", "email": "juan@test.com"},
        {"nombre": "Ana", "apellidos": "García", "email": "ana@test.com"},
    ])

    resp = await async_client.post(
        "/api/v1/padron/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("padron.csv", io.BytesIO(csv_data), "text/csv")},
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["filas_importadas"] == 2
    assert data["materia_id"] == str(materia.id)
    assert data["cohorte_id"] == str(cohorte.id)
    assert "version_id" in data


# ---------------------------------------------------------------------------
# Task 8.2 — email cifrado en DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_cifrado_en_db(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """GREEN: tras importar, email_encrypted en DB no es plaintext (es ciphertext AES-GCM)."""
    from sqlalchemy import text

    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_p2", "ADMIN")
    materia = await _create_materia(db_session, tenant_a, "MAT-P2")
    cohorte = await _create_cohorte(db_session, tenant_a, "2025-B")

    plaintext_email = "secreto@test.com"
    csv_data = _csv_bytes([
        {"nombre": "Test", "apellidos": "User", "email": plaintext_email},
    ])

    resp = await async_client.post(
        "/api/v1/padron/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("padron.csv", io.BytesIO(csv_data), "text/csv")},
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )
    assert resp.status_code == 201, resp.text

    # Consultar el ciphertext directamente en DB
    result = await db_session.execute(
        text("SELECT email_encrypted FROM entrada_padron WHERE tenant_id = :tid"),
        {"tid": tenant_a.id},
    )
    rows = result.fetchall()
    assert len(rows) == 1
    ciphertext = rows[0][0]

    # El ciphertext debe tener el formato nonce_b64:data_b64 (contiene ':')
    assert ":" in ciphertext
    # No debe contener el plaintext en ningún lugar
    assert plaintext_email not in ciphertext


# ---------------------------------------------------------------------------
# Task 8.3 — segunda importación desactiva la primera versión
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reimportar_desactiva_version_anterior(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: segunda importación crea nueva versión y desactiva la anterior."""
    from sqlalchemy import text

    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_p3", "ADMIN")
    materia = await _create_materia(db_session, tenant_a, "MAT-P3")
    cohorte = await _create_cohorte(db_session, tenant_a, "2025-C")
    headers = {"Authorization": f"Bearer {token}"}

    csv1 = _csv_bytes([{"nombre": "Juan", "apellidos": "Uno", "email": "juan1@test.com"}])
    resp1 = await async_client.post(
        "/api/v1/padron/importar",
        headers=headers,
        files={"archivo": ("v1.csv", io.BytesIO(csv1), "text/csv")},
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )
    assert resp1.status_code == 201, resp1.text
    version_id_1 = resp1.json()["version_id"]

    csv2 = _csv_bytes([{"nombre": "Ana", "apellidos": "Dos", "email": "ana2@test.com"}])
    resp2 = await async_client.post(
        "/api/v1/padron/importar",
        headers=headers,
        files={"archivo": ("v2.csv", io.BytesIO(csv2), "text/csv")},
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )
    assert resp2.status_code == 201, resp2.text
    version_id_2 = resp2.json()["version_id"]

    assert version_id_1 != version_id_2

    # Verificar en DB: la primera versión quedó inactiva
    result = await db_session.execute(
        text("SELECT id, activa FROM version_padron WHERE tenant_id = :tid ORDER BY created_at"),
        {"tid": tenant_a.id},
    )
    versions = result.fetchall()
    assert len(versions) == 2
    v1 = next(v for v in versions if str(v[0]) == version_id_1)
    v2 = next(v for v in versions if str(v[0]) == version_id_2)
    assert v1[1] is False   # desactivada
    assert v2[1] is True    # activa


# ---------------------------------------------------------------------------
# Task 8.4 — PROFESOR sin asignación vigente → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profesor_sin_asignacion_403(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: PROFESOR con padron:importar (is_own_resource=True) pero
    sin asignación vigente como PROFESOR en la materia → 403."""
    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_p4", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-P4")
    cohorte = await _create_cohorte(db_session, tenant_a, "2025-D")

    csv_data = _csv_bytes([{"nombre": "Test", "apellidos": "User", "email": "t@test.com"}])

    resp = await async_client.post(
        "/api/v1/padron/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("padron.csv", io.BytesIO(csv_data), "text/csv")},
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Task 8.5 — aislamiento multi-tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aislamiento_multi_tenant(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a, tenant_b
):
    """TRIANGULATE: admin_b no puede desactivar versión del padron de tenant_a."""
    admin_a, token_a = await _make_user_with_rol(db_session, tenant_a, "admin_p5a", "ADMIN")
    admin_b, token_b = await _make_user_with_rol(db_session, tenant_b, "admin_p5b", "ADMIN")

    materia_a = await _create_materia(db_session, tenant_a, "MAT-P5A")
    cohorte_a = await _create_cohorte(db_session, tenant_a, "2025-E")

    # Admin A importa su padrón
    csv_data = _csv_bytes([{"nombre": "Juan", "apellidos": "A", "email": "juan_a@test.com"}])
    resp = await async_client.post(
        "/api/v1/padron/importar",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"archivo": ("padron.csv", io.BytesIO(csv_data), "text/csv")},
        data={"materia_id": str(materia_a.id), "cohorte_id": str(cohorte_a.id)},
    )
    assert resp.status_code == 201, resp.text

    # Admin B intenta eliminar la versión activa de materia_a (fuera de su tenant)
    # El VersionPadronRepository filtra por tenant_id → get_activa() retorna None → 404
    resp_del = await async_client.delete(
        f"/api/v1/padron/{materia_a.id}/{cohorte_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_del.status_code == 404


# ---------------------------------------------------------------------------
# Task 8.6 — sync-moodle sin configuración → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_moodle_no_configurado_422(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: POST /padron/sync-moodle sin MOODLE_URL/TOKEN → 422."""
    admin, token = await _make_user_with_rol(db_session, tenant_a, "admin_p6", "ADMIN")
    materia = await _create_materia(db_session, tenant_a, "MAT-P6")
    cohorte = await _create_cohorte(db_session, tenant_a, "2025-F")

    resp = await async_client.post(
        "/api/v1/padron/sync-moodle",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
            "moodle_course_id": 42,
        },
    )

    # Sin MOODLE_URL ni MOODLE_TOKEN en el entorno de test → MoodleNotConfiguredError → 422
    assert resp.status_code == 422
