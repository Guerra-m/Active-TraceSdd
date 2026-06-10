"""Tests TDD para calificaciones y umbral (C-10) — tasks 8.1-8.6.

Verifica:
  8.1 — importar CSV con columnas (Real) → 201, actividades_detectadas correcto
  8.2 — campo aprobado calculado con umbral: >= umbral → True, < umbral → False
  8.3 — importar sin padrón activo → 201 (entrada_padron_id=null en DB)
  8.4 — vaciar calificaciones: PROFESOR A no afecta datos de PROFESOR B misma materia
  8.5 — GET umbral sin configuración → 200 con es_default=True y umbral_pct=60
  8.6 — PUT umbral luego GET → retorna valor configurado con es_default=False

TDD Evidence:
| Task | Layer  | Safety Net   | RED | GREEN | TRIANGULATE           |
|------|--------|--------------|-----|-------|----------------------|
| 8.1  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ 201 + actividades |
| 8.2  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ 2 casos umbral    |
| 8.3  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ sin padrón        |
| 8.4  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ scope aislado     |
| 8.5  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ default=True      |
| 8.6  | Integr | ✅ 166/166   | ✅  | ✅    | ✅ upsert y GET      |
"""

import hashlib
import io
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Cal Tenant A", slug="cal-tenant-a")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Cal Tenant B", slug="cal-tenant-b")
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


async def _create_asignacion(db_session, tenant, usuario, materia, rol: str = "PROFESOR"):
    from app.models.asignacion import Asignacion
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol=rol,
        materia_id=materia.id,
        desde=date.today(),
    )
    db_session.add(a)
    await db_session.flush()
    await db_session.refresh(a)
    await db_session.commit()
    return a


def _csv_calificaciones(rows_alumnos: list[dict], actividades: list[str]) -> bytes:
    """Genera CSV con columnas de actividad que terminan en (Real)."""
    col_headers = ["Nombre", "Apellido(s)", "Dirección de correo"]
    for act in actividades:
        col_headers.append(f"{act} (Real)")
    lines = [",".join(col_headers)]
    for row in rows_alumnos:
        values = [row.get("nombre", ""), row.get("apellidos", ""), row.get("email", "")]
        for act in actividades:
            values.append(str(row.get(act, "")))
        lines.append(",".join(values))
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# Task 8.1 — importar CSV con columnas (Real) → 201
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_importar_calificaciones_csv_201(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: POST /calificaciones/importar con CSV válido → 201, actividades_detectadas."""
    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_c1", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-C1")
    asignacion = await _create_asignacion(db_session, tenant_a, profesor, materia)

    csv_data = _csv_calificaciones(
        rows_alumnos=[
            {"nombre": "Juan", "apellidos": "Pérez", "email": "juan@test.com", "TP1": "75", "TP2": "80"},
            {"nombre": "Ana", "apellidos": "García", "email": "ana@test.com", "TP1": "50", "TP2": "90"},
        ],
        actividades=["TP1", "TP2"],
    )

    resp = await async_client.post(
        "/api/v1/calificaciones/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("calificaciones.csv", io.BytesIO(csv_data), "text/csv")},
        data={"asignacion_id": str(asignacion.id), "materia_id": str(materia.id)},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["filas_importadas"] == 4  # 2 alumnos × 2 actividades
    assert "TP1" in data["actividades_detectadas"]
    assert "TP2" in data["actividades_detectadas"]
    assert data["asignacion_id"] == str(asignacion.id)


# ---------------------------------------------------------------------------
# Task 8.2 — aprobado calculado con umbral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aprobado_calculado_con_umbral(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """GREEN: nota >= 60 → aprobado=True; nota < 60 → aprobado=False (default 60%)."""
    from sqlalchemy import text

    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_c2", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-C2")
    asignacion = await _create_asignacion(db_session, tenant_a, profesor, materia)

    csv_data = _csv_calificaciones(
        rows_alumnos=[
            {"nombre": "Aprobado", "apellidos": "User", "email": "aprobado@test.com", "TP1": "60"},
            {"nombre": "Reprobado", "apellidos": "User", "email": "reprobado@test.com", "TP1": "59"},
        ],
        actividades=["TP1"],
    )

    resp = await async_client.post(
        "/api/v1/calificaciones/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("calificaciones.csv", io.BytesIO(csv_data), "text/csv")},
        data={"asignacion_id": str(asignacion.id), "materia_id": str(materia.id)},
    )
    assert resp.status_code == 201, resp.text

    # Verificar en DB
    result = await db_session.execute(
        text(
            "SELECT nota_numerica, aprobado FROM calificaciones "
            "WHERE tenant_id = :tid ORDER BY nota_numerica DESC"
        ),
        {"tid": tenant_a.id},
    )
    rows = result.fetchall()
    assert len(rows) == 2
    # nota=60 → aprobado=True
    assert rows[0][1] is True
    # nota=59 → aprobado=False
    assert rows[1][1] is False


# ---------------------------------------------------------------------------
# Task 8.3 — importar sin padrón activo → 201, entrada_padron_id=null
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_importar_sin_padron_activo_ok(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: importar sin padrón activo → 201 con entrada_padron_id=null."""
    from sqlalchemy import text

    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_c3", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-C3")
    asignacion = await _create_asignacion(db_session, tenant_a, profesor, materia)

    csv_data = _csv_calificaciones(
        rows_alumnos=[{"nombre": "Test", "apellidos": "User", "email": "t@test.com", "TP1": "70"}],
        actividades=["TP1"],
    )

    resp = await async_client.post(
        "/api/v1/calificaciones/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("calificaciones.csv", io.BytesIO(csv_data), "text/csv")},
        data={"asignacion_id": str(asignacion.id), "materia_id": str(materia.id)},
    )
    assert resp.status_code == 201, resp.text

    result = await db_session.execute(
        text("SELECT entrada_padron_id FROM calificaciones WHERE tenant_id = :tid"),
        {"tid": tenant_a.id},
    )
    rows = result.fetchall()
    assert len(rows) == 1
    assert rows[0][0] is None  # sin padrón → null


# ---------------------------------------------------------------------------
# Task 8.4 — vaciar: scope aislado entre docentes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vaciar_calificaciones_scope_aislado(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: vaciar de PROFESOR A no afecta calificaciones de PROFESOR B."""
    from sqlalchemy import text

    materia = await _create_materia(db_session, tenant_a, "MAT-C4")
    prof_a, token_a = await _make_user_with_rol(db_session, tenant_a, "prof_c4a", "PROFESOR")
    prof_b, token_b = await _make_user_with_rol(db_session, tenant_a, "prof_c4b", "COORDINADOR")
    asig_a = await _create_asignacion(db_session, tenant_a, prof_a, materia, "PROFESOR")
    asig_b = await _create_asignacion(db_session, tenant_a, prof_b, materia, "COORDINADOR")

    # Ambos importan
    for token, asig_id in [(token_a, asig_a.id), (token_b, asig_b.id)]:
        csv_data = _csv_calificaciones(
            rows_alumnos=[{"nombre": "X", "apellidos": "Y", "email": "x@test.com", "TP1": "70"}],
            actividades=["TP1"],
        )
        r = await async_client.post(
            "/api/v1/calificaciones/importar",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("c.csv", io.BytesIO(csv_data), "text/csv")},
            data={"asignacion_id": str(asig_id), "materia_id": str(materia.id)},
        )
        assert r.status_code == 201, r.text

    # PROFESOR A vacía sus datos
    resp_del = await async_client.delete(
        f"/api/v1/calificaciones/{asig_a.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_del.status_code == 204

    # DB: solo las calificaciones de asig_b sobreviven
    result = await db_session.execute(
        text(
            "SELECT asignacion_id FROM calificaciones "
            "WHERE tenant_id = :tid AND deleted_at IS NULL"
        ),
        {"tid": tenant_a.id},
    )
    rows = result.fetchall()
    assert len(rows) == 1
    assert str(rows[0][0]) == str(asig_b.id)


# ---------------------------------------------------------------------------
# Task 8.5 — GET umbral sin configuración → es_default=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_umbral_get_default(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """RED: GET umbral sin configurar → 200 con umbral_pct=60, es_default=True."""
    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_c5", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-C5")
    asignacion = await _create_asignacion(db_session, tenant_a, profesor, materia)

    resp = await async_client.get(
        f"/api/v1/calificaciones/umbral/{asignacion.id}/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["umbral_pct"] == 60
    assert data["es_default"] is True
    assert "Satisfactorio" in data["valores_aprobatorios"]


# ---------------------------------------------------------------------------
# Task 8.6 — PUT umbral luego GET → es_default=False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_umbral_put_y_get(
    async_client: AsyncClient, db_session: AsyncSession, tenant_a
):
    """TRIANGULATE: PUT umbral → GET retorna valor configurado, es_default=False."""
    profesor, token = await _make_user_with_rol(db_session, tenant_a, "prof_c6", "PROFESOR")
    materia = await _create_materia(db_session, tenant_a, "MAT-C6")
    asignacion = await _create_asignacion(db_session, tenant_a, profesor, materia)
    headers = {"Authorization": f"Bearer {token}"}

    resp_put = await async_client.put(
        f"/api/v1/calificaciones/umbral/{asignacion.id}/{materia.id}",
        headers=headers,
        json={"umbral_pct": 75, "valores_aprobatorios": ["Aprobado", "Excelente"]},
    )
    assert resp_put.status_code == 200, resp_put.text

    resp_get = await async_client.get(
        f"/api/v1/calificaciones/umbral/{asignacion.id}/{materia.id}",
        headers=headers,
    )
    assert resp_get.status_code == 200, resp_get.text
    data = resp_get.json()
    assert data["umbral_pct"] == 75
    assert data["es_default"] is False
    assert "Aprobado" in data["valores_aprobatorios"]
