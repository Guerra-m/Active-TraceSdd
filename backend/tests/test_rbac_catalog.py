"""Tests para el catálogo RBAC: roles, permisos y matriz rol_permiso.

Suite TDD (Strict) para C-04 rbac-permisos-finos.
Verifica:
  - 7 roles del dominio existen en DB tras la migración
  - ≥21 permisos del dominio existen en DB
  - Matriz rol_permiso con is_own_resource correcto:
      PROFESOR  → calificaciones:importar con is_own_resource=True
      COORDINADOR → calificaciones:importar con is_own_resource=False
  - Formato de permisos: modulo:accion
  - NEXO existe como rol sin permisos predefinidos
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Seed fixture — inserta el catálogo base en DB (scope=function debido a
# clean_tables autouse que trunca entre tests)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac_catalog(db_session: AsyncSession):
    """Inserta el seed RBAC en cada test que lo necesite.

    El conftest.clean_tables trunca las tablas entre tests, por lo que
    el seed debe re-insertarse por cada test de este módulo.
    """
    from app.core.rbac_seed import insert_rbac_seed

    await insert_rbac_seed(db_session)


# ---------------------------------------------------------------------------
# Fixtures de consulta
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def seeded_roles(db_session: AsyncSession):
    """Devuelve todos los roles del sistema (is_system=True) desde DB."""
    from app.models.rol import Rol

    result = await db_session.execute(
        select(Rol).where(Rol.is_system.is_(True))
    )
    return result.scalars().all()


@pytest_asyncio.fixture
async def seeded_permisos(db_session: AsyncSession):
    """Devuelve todos los permisos activos desde DB."""
    from app.models.permiso import Permiso

    result = await db_session.execute(
        select(Permiso).where(Permiso.is_active.is_(True))
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Test 8.1a — 7 roles del dominio existen tras crear las tablas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seven_domain_roles_exist(db_session: AsyncSession, seeded_roles):
    """Los 7 roles del dominio deben existir con is_system=True y tenant_id=NULL."""
    role_codes = {r.code for r in seeded_roles}
    expected = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}
    assert expected == role_codes, (
        f"Roles faltantes: {expected - role_codes}, extras: {role_codes - expected}"
    )


@pytest.mark.asyncio
async def test_domain_roles_have_null_tenant(db_session: AsyncSession, seeded_roles):
    """Roles del dominio tienen tenant_id=NULL (son globales, no de un tenant)."""
    for rol in seeded_roles:
        assert rol.tenant_id is None, f"Rol {rol.code} tiene tenant_id={rol.tenant_id}, esperado NULL"


@pytest.mark.asyncio
async def test_domain_roles_are_active(db_session: AsyncSession, seeded_roles):
    """Todos los roles del dominio están activos."""
    for rol in seeded_roles:
        assert rol.is_active is True, f"Rol {rol.code} no está activo"


# ---------------------------------------------------------------------------
# Test 8.1b — ≥21 permisos del dominio existen
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_at_least_21_permisos_exist(db_session: AsyncSession, seeded_permisos):
    """La DB debe tener al menos 21 permisos del dominio."""
    assert len(seeded_permisos) >= 21, (
        f"Solo hay {len(seeded_permisos)} permisos, se esperan ≥21"
    )


@pytest.mark.asyncio
async def test_permission_codes_follow_format(db_session: AsyncSession, seeded_permisos):
    """Todos los códigos de permiso siguen el formato 'modulo:accion'."""
    for p in seeded_permisos:
        parts = p.code.split(":")
        assert len(parts) == 2, f"Permiso '{p.code}' no sigue formato modulo:accion"
        assert parts[0] and parts[1], f"Permiso '{p.code}' tiene parte vacía"


@pytest.mark.asyncio
async def test_required_domain_permissions_exist(db_session: AsyncSession, seeded_permisos):
    """Los permisos requeridos por la spec deben existir."""
    perm_codes = {p.code for p in seeded_permisos}
    required = {
        "academico:ver_propio",
        "evaluacion:reservar",
        "avisos:confirmar",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "estructura:gestionar",
        "usuarios:gestionar",
        "auditoria:ver",
        "liquidaciones:operar",
        "liquidaciones:cerrar",
        "facturas:gestionar",
        "tenant:configurar",
        "impersonacion:usar",
        "roles:ver",
    }
    missing = required - perm_codes
    assert not missing, f"Permisos faltantes: {missing}"


# ---------------------------------------------------------------------------
# Test 8.1c — Matriz rol_permiso: is_own_resource correcto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profesor_calificaciones_importar_is_own_resource_true(
    db_session: AsyncSession,
):
    """PROFESOR tiene calificaciones:importar con is_own_resource=True."""
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso

    # Obtener PROFESOR
    r_result = await db_session.execute(select(Rol).where(Rol.code == "PROFESOR"))
    profesor = r_result.scalar_one_or_none()
    assert profesor is not None, "Rol PROFESOR no existe"

    # Obtener permiso
    p_result = await db_session.execute(
        select(Permiso).where(Permiso.code == "calificaciones:importar")
    )
    perm = p_result.scalar_one_or_none()
    assert perm is not None, "Permiso calificaciones:importar no existe"

    # Verificar asignación
    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == profesor.id,
            RolPermiso.permiso_id == perm.id,
        )
    )
    rp = rp_result.scalar_one_or_none()
    assert rp is not None, "PROFESOR no tiene asignado calificaciones:importar"
    assert rp.is_own_resource is True, (
        f"PROFESOR.calificaciones:importar debe ser is_own_resource=True, "
        f"obtenido: {rp.is_own_resource}"
    )


@pytest.mark.asyncio
async def test_coordinador_calificaciones_importar_is_own_resource_false(
    db_session: AsyncSession,
):
    """COORDINADOR tiene calificaciones:importar con is_own_resource=False."""
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso

    r_result = await db_session.execute(select(Rol).where(Rol.code == "COORDINADOR"))
    coordinador = r_result.scalar_one_or_none()
    assert coordinador is not None, "Rol COORDINADOR no existe"

    p_result = await db_session.execute(
        select(Permiso).where(Permiso.code == "calificaciones:importar")
    )
    perm = p_result.scalar_one_or_none()
    assert perm is not None

    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == coordinador.id,
            RolPermiso.permiso_id == perm.id,
        )
    )
    rp = rp_result.scalar_one_or_none()
    assert rp is not None, "COORDINADOR no tiene asignado calificaciones:importar"
    assert rp.is_own_resource is False, (
        f"COORDINADOR.calificaciones:importar debe ser is_own_resource=False, "
        f"obtenido: {rp.is_own_resource}"
    )


@pytest.mark.asyncio
async def test_nexo_has_no_predefined_permissions(db_session: AsyncSession):
    """NEXO existe como rol pero no tiene permisos predefinidos."""
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    r_result = await db_session.execute(select(Rol).where(Rol.code == "NEXO"))
    nexo = r_result.scalar_one_or_none()
    assert nexo is not None, "Rol NEXO no existe"

    rp_result = await db_session.execute(
        select(RolPermiso).where(RolPermiso.rol_id == nexo.id)
    )
    nexo_perms = rp_result.scalars().all()
    assert len(nexo_perms) == 0, (
        f"NEXO no debe tener permisos predefinidos, tiene: {len(nexo_perms)}"
    )
