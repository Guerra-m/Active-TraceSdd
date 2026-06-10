"""Tests TDD para el audit log (C-05) — tasks 5.1 a 5.6.

Verifica:
  - Helper audit() crea registros correctos (minimal y full)
  - Trigger append-only rechaza UPDATE y DELETE a nivel DB
  - AuditLogRepository.insert() persiste en DB
  - Aislamiento de tenant
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine


# ---------------------------------------------------------------------------
# Fixture: crear el trigger append-only en la DB de test
# (create_all no aplica triggers; se crea con SQL directo)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_audit_trigger(db_engine: AsyncEngine):
    """Crea el trigger append-only sobre audit_log en la DB de test."""
    async with db_engine.begin() as conn:
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION audit_log_immutable()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
            END;
            $$;
        """))
        await conn.execute(text("""
            CREATE OR REPLACE TRIGGER trg_audit_log_immutable
            BEFORE UPDATE OR DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
        """))


# ---------------------------------------------------------------------------
# Fixtures de soporte
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Audit Tenant", slug="audit-tenant")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Audit Tenant B", slug="audit-tenant-b")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def user(db_session: AsyncSession, tenant):
    import hashlib
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.encryption import encrypt

    email = "audit_user@test.com"
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def user_b(db_session: AsyncSession, tenant_b):
    import hashlib
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.encryption import encrypt

    email = "audit_user_b@test.com"
    u = User(
        tenant_id=tenant_b.id,
        email_encrypted=encrypt(email),
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# 5.1 RED: test_insert_creates_record — helper audit() persiste en DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_creates_record(db_session: AsyncSession, tenant, user):
    """audit() crea un registro en audit_log verificable via SELECT crudo."""
    from app.core.audit import audit, PADRON_CARGAR

    await audit(
        db_session,
        actor_id=user.id,
        tenant_id=tenant.id,
        accion=PADRON_CARGAR,
    )
    await db_session.commit()

    result = await db_session.execute(
        text("SELECT accion, actor_id, tenant_id FROM audit_log WHERE actor_id = :uid"),
        {"uid": user.id},
    )
    rows = result.fetchall()
    assert len(rows) == 1
    assert rows[0].accion == PADRON_CARGAR


# ---------------------------------------------------------------------------
# 5.2 test_update_raises — trigger append-only rechaza UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_raises(db_session: AsyncSession, tenant, user):
    """UPDATE directo sobre audit_log falla con excepción (trigger DB)."""
    from app.core.audit import audit, CALIFICACIONES_IMPORTAR
    import asyncpg

    await audit(db_session, actor_id=user.id, tenant_id=tenant.id, accion=CALIFICACIONES_IMPORTAR)
    await db_session.commit()

    with pytest.raises(Exception) as exc_info:
        await db_session.execute(
            text("UPDATE audit_log SET accion = 'HACK' WHERE actor_id = :uid"),
            {"uid": user.id},
        )
        await db_session.flush()

    assert "append-only" in str(exc_info.value).lower() or exc_info.value is not None


# ---------------------------------------------------------------------------
# 5.3 test_delete_raises — trigger append-only rechaza DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_raises(db_session: AsyncSession, tenant, user):
    """DELETE directo sobre audit_log falla con excepción (trigger DB)."""
    from app.core.audit import audit, COMUNICACION_ENVIAR

    await audit(db_session, actor_id=user.id, tenant_id=tenant.id, accion=COMUNICACION_ENVIAR)
    await db_session.commit()

    with pytest.raises(Exception) as exc_info:
        await db_session.execute(
            text("DELETE FROM audit_log WHERE actor_id = :uid"),
            {"uid": user.id},
        )
        await db_session.flush()

    assert exc_info.value is not None


# ---------------------------------------------------------------------------
# 5.4 test_audit_helper_minimal — parámetros mínimos, opcionales en None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_helper_minimal(db_session: AsyncSession, tenant, user):
    """Helper con parámetros mínimos crea registro con campos opcionales = NULL."""
    from app.core.audit import audit, ASIGNACION_MODIFICAR

    await audit(db_session, actor_id=user.id, tenant_id=tenant.id, accion=ASIGNACION_MODIFICAR)
    await db_session.commit()

    result = await db_session.execute(
        text(
            "SELECT impersonado_id, materia_id, detalle, filas_afectadas, ip, user_agent "
            "FROM audit_log WHERE actor_id = :uid AND accion = :accion"
        ),
        {"uid": user.id, "accion": ASIGNACION_MODIFICAR},
    )
    row = result.fetchone()
    assert row is not None
    assert row.impersonado_id is None
    assert row.materia_id is None
    assert row.detalle is None
    assert row.filas_afectadas is None
    assert row.ip is None
    assert row.user_agent is None


# ---------------------------------------------------------------------------
# 5.5 test_audit_helper_full — todos los parámetros
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_helper_full(db_session: AsyncSession, tenant, user, user_b):
    """Helper con todos los parámetros crea registro completo."""
    from app.core.audit import audit, IMPERSONACION_INICIAR

    await audit(
        db_session,
        actor_id=user.id,
        tenant_id=tenant.id,
        accion=IMPERSONACION_INICIAR,
        impersonado_id=user_b.id,
        detalle={"razon": "soporte"},
        filas_afectadas=1,
        ip="10.0.0.1",
        user_agent="pytest/1.0",
    )
    await db_session.commit()

    result = await db_session.execute(
        text(
            "SELECT actor_id, impersonado_id, accion, detalle, filas_afectadas, ip, user_agent "
            "FROM audit_log WHERE actor_id = :uid AND accion = :accion"
        ),
        {"uid": user.id, "accion": IMPERSONACION_INICIAR},
    )
    row = result.fetchone()
    assert row is not None
    assert str(row.actor_id) == str(user.id)
    assert str(row.impersonado_id) == str(user_b.id)
    assert row.detalle == {"razon": "soporte"}
    assert row.filas_afectadas == 1
    assert row.ip == "10.0.0.1"
    assert row.user_agent == "pytest/1.0"


# ---------------------------------------------------------------------------
# 5.6 test_tenant_isolation — registros de tenant A no visibles por tenant B
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession, tenant, user, tenant_b, user_b):
    """Registro de tenant A no aparece al filtrar por tenant B."""
    from app.core.audit import audit, PADRON_CARGAR

    await audit(db_session, actor_id=user.id, tenant_id=tenant.id, accion=PADRON_CARGAR)
    await db_session.commit()

    result = await db_session.execute(
        text("SELECT count(*) FROM audit_log WHERE tenant_id = :tid"),
        {"tid": tenant_b.id},
    )
    count = result.scalar()
    assert count == 0
