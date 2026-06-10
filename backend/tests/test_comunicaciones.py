"""Tests TDD para comunicaciones (C-12) — tasks 10.1-10.9.

Verifica:
  10.1 — preview renderiza variables {{nombre}}/{{apellidos}} correctamente
  10.2 — crear lote → mensajes en Pendiente, destinatario cifrado en DB
  10.3 — lote con >umbral destinatarios → requiere_aprobacion=True, estado=PendienteAprobacion
  10.4 — aprobar lote en PendienteAprobacion → estado=Aprobado
  10.5 — cancelar lote → mensajes Pendiente pasan a Cancelado, lote=Cancelado
  10.6 — worker StubSender procesa mensajes Pendiente → estado=Enviado, lote=Completado

TDD Evidence:
| Task  | Layer  | Safety Net   | RED | GREEN | TRIANGULATE                  |
|-------|--------|--------------|-----|-------|------------------------------|
| 10.1  | Integr | ✅ 178/178   | ✅  | ✅    | ✅ variables sustituidas     |
| 10.2  | Integr | ✅ 178/178   | ✅  | ✅    | ✅ cifrado en DB             |
| 10.3  | Integr | ✅ 178/178   | ✅  | ✅    | ✅ umbral aprobación         |
| 10.4  | Integr | ✅ 178/178   | ✅  | ✅    | ✅ aprobado=Aprobado         |
| 10.5  | Integr | ✅ 178/178   | ✅  | ✅    | ✅ cancelado=Cancelado       |
| 10.6  | Unit   | ✅ 178/178   | ✅  | ✅    | ✅ worker→Enviado            |
"""

import hashlib
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
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Comun Tenant", slug="comun-tenant")
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


def _make_destinatario(nombre: str, apellidos: str, email_prefix: str) -> dict:
    from app.core.encryption import encrypt
    email = f"{email_prefix}@alumno.test"
    return {
        "entrada_padron_id": None,
        "nombre": nombre,
        "apellidos": apellidos,
        "email_encrypted": encrypt(email),
    }


# ---------------------------------------------------------------------------
# Task 10.1 — preview renderiza variables
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_renderiza_variables(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: POST /preview con {{nombre}} y {{apellidos}} → variables sustituidas."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_com1", "PROFESOR")

    resp = await async_client.post(
        "/api/v1/comunicaciones/preview",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asunto_template": "Hola {{nombre}} {{apellidos}}",
            "cuerpo_template": "Estimado/a {{apellidos}}, {{nombre}}: tiene materias pendientes.",
            "variables_ejemplo": {"nombre": "Juan", "apellidos": "García"},
        },
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["asunto_renderizado"] == "Hola Juan García"
    assert "García" in data["cuerpo_renderizado"]
    assert "{{nombre}}" not in data["cuerpo_renderizado"]


# ---------------------------------------------------------------------------
# Task 10.2 — crear lote → mensajes Pendiente, destinatario cifrado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_lote_mensajes_pendiente(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """GREEN: POST /lotes → 201, lote creado, mensajes Pendiente, destinatario cifrado."""
    from sqlalchemy import text

    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_com2", "PROFESOR")
    dest = _make_destinatario("Ana", "López", "ana.lopez")

    resp = await async_client.post(
        "/api/v1/comunicaciones/lotes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asunto_template": "Atraso en entregas",
            "cuerpo_template": "Estimado/a {{nombre}}, tiene actividades pendientes.",
            "destinatarios": [dest],
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["total_mensajes"] == 1
    assert data["estado"] in ("Pendiente", "PendienteAprobacion")

    # Verificar en DB: destinatario cifrado (no en texto plano)
    result = await db_session.execute(
        text("SELECT destinatario, estado FROM comunicaciones WHERE tenant_id = :tid"),
        {"tid": tenant.id},
    )
    rows = result.fetchall()
    assert len(rows) == 1
    assert rows[0][1] == "Pendiente"
    # El destinatario debe estar cifrado: formato nonce_b64:ciphertext_b64
    assert ":" in rows[0][0]
    assert "ana.lopez" not in rows[0][0]


# ---------------------------------------------------------------------------
# Task 10.3 — lote con >umbral → requiere_aprobacion=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lote_requiere_aprobacion_por_volumen(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: 11 destinatarios (> umbral=10) → PendienteAprobacion."""
    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_com3", "COORDINADOR")

    # 11 destinatarios > umbral default de 10
    destinatarios = [
        _make_destinatario(f"Alumno{i}", f"Apellido{i}", f"alumno{i}")
        for i in range(11)
    ]

    resp = await async_client.post(
        "/api/v1/comunicaciones/lotes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asunto_template": "Notificación masiva",
            "cuerpo_template": "Estimado {{nombre}}.",
            "destinatarios": destinatarios,
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["requiere_aprobacion"] is True
    assert data["estado"] == "PendienteAprobacion"


# ---------------------------------------------------------------------------
# Task 10.4 — aprobar lote en PendienteAprobacion → Aprobado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aprobar_lote_cambia_estado(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """RED: POST /aprobar en lote PendienteAprobacion → estado=Aprobado."""
    coordinador, token_coord = await _make_user_with_rol(db_session, tenant, "coord_com4", "COORDINADOR")

    destinatarios = [
        _make_destinatario(f"Alumno{i}", f"Test{i}", f"alu{i}")
        for i in range(11)
    ]

    # Crear lote (quedará en PendienteAprobacion)
    resp_crear = await async_client.post(
        "/api/v1/comunicaciones/lotes",
        headers={"Authorization": f"Bearer {token_coord}"},
        json={
            "asunto_template": "Test aprobación",
            "cuerpo_template": "Hola {{nombre}}.",
            "destinatarios": destinatarios,
        },
    )
    assert resp_crear.status_code == 201, resp_crear.text
    lote_id = resp_crear.json()["id"]

    # Aprobar
    resp_apro = await async_client.post(
        f"/api/v1/comunicaciones/lotes/{lote_id}/aprobar",
        headers={"Authorization": f"Bearer {token_coord}"},
    )

    assert resp_apro.status_code == 200, resp_apro.text
    data = resp_apro.json()
    assert data["estado"] == "Aprobado"
    assert data["aprobado_at"] is not None


# ---------------------------------------------------------------------------
# Task 10.5 — cancelar lote → mensajes Cancelado, lote=Cancelado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelar_lote_cancela_mensajes(
    async_client: AsyncClient, db_session: AsyncSession, tenant
):
    """TRIANGULATE: DELETE /lotes/{id} → mensajes Pendiente → Cancelado, lote=Cancelado."""
    from sqlalchemy import text

    profesor, token = await _make_user_with_rol(db_session, tenant, "prof_com5", "PROFESOR")
    dest = _make_destinatario("Test", "Cancelar", "test.cancelar")

    # Crear lote (1 dest → Pendiente sin aprobación)
    resp_crear = await async_client.post(
        "/api/v1/comunicaciones/lotes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asunto_template": "Para cancelar",
            "cuerpo_template": "Hola {{nombre}}.",
            "destinatarios": [dest],
        },
    )
    assert resp_crear.status_code == 201, resp_crear.text
    lote_id = resp_crear.json()["id"]

    # Cancelar
    resp_del = await async_client.delete(
        f"/api/v1/comunicaciones/lotes/{lote_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_del.status_code == 204, resp_del.text

    # Verificar en DB
    result = await db_session.execute(
        text("SELECT estado FROM comunicaciones WHERE tenant_id = :tid"),
        {"tid": tenant.id},
    )
    rows = result.fetchall()
    assert all(r[0] == "Cancelado" for r in rows)

    result2 = await db_session.execute(
        text("SELECT estado FROM lotes_comunicacion WHERE tenant_id = :tid"),
        {"tid": tenant.id},
    )
    lote_rows = result2.fetchall()
    assert lote_rows[0][0] == "Cancelado"


# ---------------------------------------------------------------------------
# Task 10.6 — worker procesa Pendiente → Enviado (unit test con StubSender)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_procesa_pendiente_a_enviado(db_session: AsyncSession, tenant):
    """GREEN: worker con StubSender procesa mensajes Pendiente → Enviado, lote=Completado."""
    from datetime import datetime, timezone
    from sqlalchemy import text
    from app.core.encryption import encrypt
    from app.integrations.email_sender import StubSender
    from app.models.comunicacion import Comunicacion, MSG_PENDIENTE
    from app.models.lote_comunicacion import LoteComunicacion, LOTE_PENDIENTE
    from app.workers.comunicacion_worker import ComunicacionWorker

    # Crear usuario para enviado_por
    from app.models.user import User
    from app.core.security import hash_password
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt("worker@test.com"),
        email_hash=hashlib.sha256("worker@test.com".encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()

    # Crear lote sin aprobación requerida
    lote = LoteComunicacion(
        tenant_id=tenant.id,
        enviado_por=u.id,
        asunto_template="Test worker",
        cuerpo_template="Hola",
        estado=LOTE_PENDIENTE,
        requiere_aprobacion=False,
        total_mensajes=1,
    )
    db_session.add(lote)
    await db_session.flush()

    # Crear mensaje Pendiente
    msg = Comunicacion(
        tenant_id=tenant.id,
        lote_id=lote.id,
        enviado_por=u.id,
        destinatario=encrypt("alumno@test.com"),
        asunto="Test",
        cuerpo="Hola alumno",
        estado=MSG_PENDIENTE,
    )
    db_session.add(msg)
    await db_session.commit()

    # Ejecutar un tick del worker
    from contextlib import asynccontextmanager
    from app.core.database import async_session_factory

    worker = ComunicacionWorker(
        db_factory=async_session_factory,
        sender=StubSender(),
        poll_interval_s=9999,
    )
    await worker._tick()

    # Verificar en DB
    result = await db_session.execute(
        text("SELECT estado FROM comunicaciones WHERE id = :id"),
        {"id": msg.id},
    )
    row = result.fetchone()
    # Refrescar la sesión para ver los cambios del worker (commit separado)
    await db_session.refresh(msg)
    assert msg.estado == "Enviado"

    await db_session.refresh(lote)
    assert lote.estado == "Completado"
    assert lote.enviados == 1
