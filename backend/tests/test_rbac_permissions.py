"""Tests para la resolución de permisos efectivos via RbacService.

Suite TDD (Strict) para C-04 rbac-permisos-finos — tareas 8.2-8.5.
Verifica:
  - Usuario sin roles → set vacío
  - Usuario con un rol → permisos del rol
  - Usuario con dos roles → unión correcta
  - Permiso global prevalece sobre is_own_resource=True
  - valid_until en el pasado → NO aparece
  - valid_from en el futuro → NO aparece
  - Aislamiento de tenant (8.9)
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _today() -> date:
    return date.today()


def _past() -> date:
    return _today() - timedelta(days=10)


def _future() -> date:
    return _today() + timedelta(days=10)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(db_session: AsyncSession):
    """Seed RBAC para todos los tests de este módulo."""
    from app.core.rbac_seed import insert_rbac_seed
    await insert_rbac_seed(db_session)


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant A Perms", slug="tenant-a-perms")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Tenant B Perms", slug="tenant-b-perms")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def user_a(db_session: AsyncSession, tenant_a):
    from app.models.user import User
    from app.core.encryption import encrypt
    import hashlib

    email = "user_a_perms@test.com"
    email_hash = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    u = User(
        tenant_id=tenant_a.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
        password_hash="hashed",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def user_b(db_session: AsyncSession, tenant_b):
    from app.models.user import User
    from app.core.encryption import encrypt
    import hashlib

    email = "user_b_perms@test.com"
    email_hash = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    u = User(
        tenant_id=tenant_b.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
        password_hash="hashed",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


async def _get_rol(db_session, code: str):
    from sqlalchemy import select
    from app.models.rol import Rol
    result = await db_session.execute(select(Rol).where(Rol.code == code))
    return result.scalar_one()


async def _assign_rol(db_session, user, rol, tenant,
                      valid_from=None, valid_until=None):
    from app.models.usuario_rol import UsuarioRol
    ur = UsuarioRol(
        tenant_id=tenant.id,
        user_id=user.id,
        rol_id=rol.id,
        valid_from=valid_from or _today(),
        valid_until=valid_until,
    )
    db_session.add(ur)
    await db_session.flush()
    return ur


# ---------------------------------------------------------------------------
# Test 8.2 — Usuario sin roles → set vacío
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_without_roles_has_empty_permissions(
    db_session: AsyncSession, user_a, tenant_a
):
    """Usuario sin ninguna asignación de rol tiene set vacío de permisos."""
    from app.services.rbac_service import RbacService

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )
    assert result == set(), f"Esperado set vacío, obtenido: {result}"


# ---------------------------------------------------------------------------
# Test 8.2 — Usuario con un rol → permisos del rol
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_with_one_role_gets_role_permissions(
    db_session: AsyncSession, user_a, tenant_a
):
    """Usuario con rol ALUMNO obtiene exactamente los permisos de ALUMNO."""
    from app.services.rbac_service import RbacService

    alumno = await _get_rol(db_session, "ALUMNO")
    await _assign_rol(db_session, user_a, alumno, tenant_a)

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )

    perm_codes = {code for code, _ in result}
    expected = {"academico:ver_propio", "evaluacion:reservar", "avisos:confirmar"}
    assert expected == perm_codes, (
        f"Permisos inesperados. Esperados: {expected}, obtenidos: {perm_codes}"
    )


# ---------------------------------------------------------------------------
# Test 8.2 — Usuario con dos roles → unión correcta
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_with_two_roles_gets_union_of_permissions(
    db_session: AsyncSession, user_a, tenant_a
):
    """Usuario con ALUMNO + TUTOR obtiene la unión de ambos sets de permisos."""
    from app.services.rbac_service import RbacService

    alumno = await _get_rol(db_session, "ALUMNO")
    tutor = await _get_rol(db_session, "TUTOR")
    await _assign_rol(db_session, user_a, alumno, tenant_a)
    await _assign_rol(db_session, user_a, tutor, tenant_a)

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )

    perm_codes = {code for code, _ in result}
    # ALUMNO tiene: academico:ver_propio, evaluacion:reservar, avisos:confirmar
    # TUTOR tiene: avisos:confirmar, atrasados:ver, entregas:ver, encuentros:gestionar, guardias:registrar
    assert "academico:ver_propio" in perm_codes   # de ALUMNO
    assert "evaluacion:reservar" in perm_codes    # de ALUMNO
    assert "atrasados:ver" in perm_codes          # de TUTOR
    assert "encuentros:gestionar" in perm_codes   # de TUTOR
    # avisos:confirmar está en ambos — debe aparecer una sola vez
    assert "avisos:confirmar" in perm_codes


# ---------------------------------------------------------------------------
# Test 8.3 — Permiso global prevalece sobre is_own_resource=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_permission_prevails_over_own_resource(
    db_session: AsyncSession, user_a, tenant_a
):
    """PROFESOR (is_own_resource=True) + COORDINADOR (is_own_resource=False)
    en calificaciones:importar → resultado es is_own_resource=False."""
    from app.services.rbac_service import RbacService

    profesor = await _get_rol(db_session, "PROFESOR")
    coordinador = await _get_rol(db_session, "COORDINADOR")
    await _assign_rol(db_session, user_a, profesor, tenant_a)
    await _assign_rol(db_session, user_a, coordinador, tenant_a)

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )

    cal_importar = {(c, own) for c, own in result if c == "calificaciones:importar"}
    assert len(cal_importar) == 1, "calificaciones:importar debe aparecer exactamente una vez"
    code, is_own = next(iter(cal_importar))
    assert is_own is False, (
        f"Con PROFESOR+COORDINADOR, calificaciones:importar debe ser is_own_resource=False, "
        f"obtenido: {is_own}"
    )


# ---------------------------------------------------------------------------
# Test 8.4 — valid_until en el pasado → NO aparece
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_role_assignment_not_included(
    db_session: AsyncSession, user_a, tenant_a
):
    """Asignación con valid_until en el pasado NO otorga permisos."""
    from app.services.rbac_service import RbacService

    alumno = await _get_rol(db_session, "ALUMNO")
    await _assign_rol(
        db_session, user_a, alumno, tenant_a,
        valid_from=_past() - timedelta(days=30),
        valid_until=_past(),  # expirado hace 10 días
    )

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )
    assert result == set(), (
        f"Asignación expirada no debe otorgar permisos, obtenido: {result}"
    )


# ---------------------------------------------------------------------------
# Test 8.5 — valid_from en el futuro → NO aparece
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_future_role_assignment_not_included(
    db_session: AsyncSession, user_a, tenant_a
):
    """Asignación con valid_from en el futuro NO otorga permisos todavía."""
    from app.services.rbac_service import RbacService

    alumno = await _get_rol(db_session, "ALUMNO")
    await _assign_rol(
        db_session, user_a, alumno, tenant_a,
        valid_from=_future(),  # empieza en 10 días
        valid_until=None,
    )

    result = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )
    assert result == set(), (
        f"Asignación futura no debe otorgar permisos, obtenido: {result}"
    )


# ---------------------------------------------------------------------------
# Test 8.9 — Aislamiento de tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_permissions(
    db_session: AsyncSession, user_a, user_b, tenant_a, tenant_b
):
    """Usuario de tenant A no puede usar roles/permisos de tenant B."""
    from app.services.rbac_service import RbacService

    # Asignar ADMIN al user_a en tenant_a
    admin = await _get_rol(db_session, "ADMIN")
    await _assign_rol(db_session, user_a, admin, tenant_a)

    # user_b en tenant_b sin roles
    # Consultar permisos de user_a con tenant_id=tenant_b (cruce incorrecto)
    result_cross = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_b.id,  # tenant incorrecto
        db=db_session,
    )
    assert result_cross == set(), (
        "Usuario de tenant A no debe tener permisos en tenant B"
    )

    # user_a en su propio tenant sí tiene permisos
    result_own = await RbacService.get_effective_permissions(
        user_id=user_a.id,
        tenant_id=tenant_a.id,
        db=db_session,
    )
    assert len(result_own) > 0, "user_a debe tener permisos en su propio tenant"
