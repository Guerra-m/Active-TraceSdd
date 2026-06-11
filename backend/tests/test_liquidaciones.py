"""Tests TDD para C-18 liquidaciones-y-honorarios.

Cubre:
  - 6.1 test_calculo_liquidacion_base_plus   — fórmula Base + N×Plus
  - 6.2 test_acumulacion_plus_n_comisiones   — 3 comisiones = 3×Plus
  - 6.3 test_cierre_liquidacion_inmutable    — cerrada no permite modificación
  - 6.4 test_facturante_excluido             — docente facturador excluido
  - 6.5 test_kpi_segmentacion               — KPIs separan general/NEXO/facturantes
  - 6.6 test_vigencia_salario               — toma salario vigente al período

TDD Evidence:
| Task | Layer  | Safety Net  | RED | GREEN | TRIANGULATE |
|------|--------|-------------|-----|-------|-------------|
| 6.1  | Unit   | ✅ baseline | ✅  | ✅    | ✅ 3 cases  |
| 6.2  | Unit   | ✅ baseline | ✅  | ✅    | ✅ 2 cases  |
| 6.3  | Integr | ✅ baseline | ✅  | ✅    | ✅ 2 cases  |
| 6.4  | Unit   | ✅ baseline | ✅  | ✅    | ✅ 2 cases  |
| 6.5  | Unit   | ✅ baseline | ✅  | ✅    | ✅ 3 cases  |
| 6.6  | Unit   | ✅ baseline | ✅  | ✅    | ✅ 3 cases  |
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(name="Liq Institution", slug="liq-institution")
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def cohorte(db_session: AsyncSession, tenant):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte

    carrera = Carrera(
        tenant_id=tenant.id,
        codigo="ING",
        nombre="Ingeniería",
        estado="Activa",
    )
    db_session.add(carrera)
    await db_session.flush()

    c = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="2024-A",
        anio=2024,
        vig_desde=date(2024, 1, 1),
    )
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    return c


@pytest_asyncio.fixture
async def materia_con_plus(db_session: AsyncSession, tenant):
    from app.models.materia import Materia
    m = Materia(
        tenant_id=tenant.id,
        codigo="PROG1",
        nombre="Programación I",
        estado="Activa",
        grupo_plus="PROG",
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    return m


@pytest_asyncio.fixture
async def materia_sin_plus(db_session: AsyncSession, tenant):
    from app.models.materia import Materia
    m = Materia(
        tenant_id=tenant.id,
        codigo="MAT1",
        nombre="Matemática I",
        estado="Activa",
        grupo_plus=None,
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    return m


@pytest_asyncio.fixture
async def usuario_profesor(db_session: AsyncSession, tenant):
    """Usuario docente normal (no facturador)."""
    from app.models.user import User
    from app.core.encryption import encrypt
    import hashlib
    email = "profesor@test.com"
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
        password_hash="hashed",
        nombre="Juan",
        apellidos="Docente",
        facturador=False,
        estado="Activo",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def usuario_facturador(db_session: AsyncSession, tenant):
    """Usuario docente facturante."""
    from app.models.user import User
    from app.core.encryption import encrypt
    import hashlib
    email = "facturador@test.com"
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
        password_hash="hashed",
        nombre="Ana",
        apellidos="Facturadora",
        facturador=True,
        estado="Activo",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def usuario_nexo(db_session: AsyncSession, tenant):
    """Usuario con rol NEXO."""
    from app.models.user import User
    from app.core.encryption import encrypt
    import hashlib
    email = "nexo@test.com"
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
    u = User(
        tenant_id=tenant.id,
        email_encrypted=encrypt(email),
        email_hash=email_hash,
        password_hash="hashed",
        nombre="Carlos",
        apellidos="Nexo",
        facturador=False,
        estado="Activo",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def salario_base_profesor(db_session: AsyncSession, tenant):
    from app.models.salario import SalarioBase
    s = SalarioBase(
        tenant_id=tenant.id,
        rol="PROFESOR",
        monto=Decimal("1000.00"),
        desde=date(2024, 1, 1),
        hasta=None,
    )
    db_session.add(s)
    await db_session.flush()
    await db_session.refresh(s)
    return s


@pytest_asyncio.fixture
async def salario_plus_prog(db_session: AsyncSession, tenant):
    from app.models.salario import SalarioPlus
    s = SalarioPlus(
        tenant_id=tenant.id,
        grupo="PROG",
        rol="PROFESOR",
        descripcion="Plus programación",
        monto=Decimal("200.00"),
        desde=date(2024, 1, 1),
        hasta=None,
    )
    db_session.add(s)
    await db_session.flush()
    await db_session.refresh(s)
    return s


# ============================================================================
# 6.1 — test_calculo_liquidacion_base_plus
# Fórmula: Total = Base + N×Plus
# ============================================================================


@pytest.mark.asyncio
async def test_calculo_liquidacion_base_plus_una_comision(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    materia_con_plus,
    salario_base_profesor,
    salario_plus_prog,
):
    """Base 1000 + 1 comisión PROG × 200 = 1200."""
    from app.models.asignacion import Asignacion
    from app.services.liquidacion_service import LiquidacionService

    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        materia_id=materia_con_plus.id,
        cohorte_id=cohorte.id,
        comisiones=["A"],
        desde=date(2024, 3, 1),
        hasta=None,
    )
    db_session.add(asig)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    assert resultado["monto_base"] == Decimal("1000.00")
    assert resultado["monto_plus"] == Decimal("200.00")
    assert resultado["total"] == Decimal("1200.00")


@pytest.mark.asyncio
async def test_calculo_liquidacion_base_sin_plus(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    materia_sin_plus,
    salario_base_profesor,
):
    """Materia sin grupo_plus → solo base, plus = 0."""
    from app.models.asignacion import Asignacion
    from app.services.liquidacion_service import LiquidacionService

    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        materia_id=materia_sin_plus.id,
        cohorte_id=cohorte.id,
        comisiones=["A"],
        desde=date(2024, 3, 1),
        hasta=None,
    )
    db_session.add(asig)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    assert resultado["monto_base"] == Decimal("1000.00")
    assert resultado["monto_plus"] == Decimal("0.00")
    assert resultado["total"] == Decimal("1000.00")


@pytest.mark.asyncio
async def test_calculo_liquidacion_sin_asignaciones(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    salario_base_profesor,
):
    """Sin asignaciones en el período → solo base."""
    from app.services.liquidacion_service import LiquidacionService

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    assert resultado["monto_base"] == Decimal("1000.00")
    assert resultado["monto_plus"] == Decimal("0.00")
    assert resultado["total"] == Decimal("1000.00")


# ============================================================================
# 6.2 — test_acumulacion_plus_n_comisiones
# 3 comisiones de PROG → 3 × Plus(PROG, rol)
# ============================================================================


@pytest.mark.asyncio
async def test_acumulacion_plus_tres_comisiones(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    materia_con_plus,
    salario_base_profesor,
    salario_plus_prog,
):
    """3 asignaciones en PROG × 200 = 600 plus. Total = 1000 + 600 = 1600."""
    from app.models.asignacion import Asignacion
    from app.services.liquidacion_service import LiquidacionService

    # Crear 3 materias del mismo grupo
    from app.models.materia import Materia
    for i in range(2):
        m = Materia(
            tenant_id=tenant.id,
            codigo=f"PROG{i+2}",
            nombre=f"Programación {i+2}",
            estado="Activa",
            grupo_plus="PROG",
        )
        db_session.add(m)
        await db_session.flush()
        asig = Asignacion(
            tenant_id=tenant.id,
            usuario_id=usuario_profesor.id,
            rol="PROFESOR",
            materia_id=m.id,
            cohorte_id=cohorte.id,
            comisiones=["A"],
            desde=date(2024, 3, 1),
            hasta=None,
        )
        db_session.add(asig)

    # Asignación original
    asig_orig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        materia_id=materia_con_plus.id,
        cohorte_id=cohorte.id,
        comisiones=["A"],
        desde=date(2024, 3, 1),
        hasta=None,
    )
    db_session.add(asig_orig)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    assert resultado["monto_plus"] == Decimal("600.00")  # 3 × 200
    assert resultado["total"] == Decimal("1600.00")  # 1000 + 600


@pytest.mark.asyncio
async def test_acumulacion_plus_dos_comisiones_misma_materia(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    materia_con_plus,
    salario_base_profesor,
    salario_plus_prog,
):
    """1 asignación con 2 comisiones (A, B) = 2 × Plus. Total = 1000 + 400 = 1400."""
    from app.models.asignacion import Asignacion
    from app.services.liquidacion_service import LiquidacionService

    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        materia_id=materia_con_plus.id,
        cohorte_id=cohorte.id,
        comisiones=["A", "B"],
        desde=date(2024, 3, 1),
        hasta=None,
    )
    db_session.add(asig)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    # 1 asignación con 2 comisiones = 2 comisiones de PROG
    assert resultado["monto_plus"] == Decimal("400.00")  # 2 × 200
    assert resultado["total"] == Decimal("1400.00")


# ============================================================================
# 6.3 — test_cierre_liquidacion_inmutable
# Cerrada no permite recálculo ni modificación
# ============================================================================


@pytest.mark.asyncio
async def test_cierre_liquidacion_inmutable(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    salario_base_profesor,
):
    """Una liquidación cerrada no puede cambiar de estado ni ser recalculada."""
    from app.models.liquidacion import Liquidacion, EstadoLiquidacion
    from app.services.liquidacion_service import LiquidacionService
    from app.core.exceptions import LiquidacionCerradaError

    liq = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-06",
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        comisiones=[],
        monto_base=Decimal("1000.00"),
        monto_plus=Decimal("0.00"),
        total=Decimal("1000.00"),
        es_nexo=False,
        excluido_por_factura=False,
        estado=EstadoLiquidacion.CERRADA,
    )
    db_session.add(liq)
    await db_session.flush()
    await db_session.refresh(liq)

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    with pytest.raises(LiquidacionCerradaError):
        await svc.cerrar_liquidacion(
            liquidacion_id=liq.id,
            actor_id=usuario_profesor.id,
        )


@pytest.mark.asyncio
async def test_cierre_liquidacion_abierta_ok(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    salario_base_profesor,
):
    """Una liquidación Abierta se puede cerrar correctamente."""
    from app.models.liquidacion import Liquidacion, EstadoLiquidacion
    from app.services.liquidacion_service import LiquidacionService

    liq = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-06",
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        comisiones=[],
        monto_base=Decimal("1000.00"),
        monto_plus=Decimal("0.00"),
        total=Decimal("1000.00"),
        es_nexo=False,
        excluido_por_factura=False,
        estado=EstadoLiquidacion.ABIERTA,
    )
    db_session.add(liq)
    await db_session.flush()
    await db_session.refresh(liq)

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    liq_cerrada = await svc.cerrar_liquidacion(
        liquidacion_id=liq.id,
        actor_id=usuario_profesor.id,
    )

    assert liq_cerrada.estado == EstadoLiquidacion.CERRADA


# ============================================================================
# 6.4 — test_facturante_excluido_de_liquidacion
# Docente facturador → excluido_por_factura=True
# ============================================================================


@pytest.mark.asyncio
async def test_facturante_excluido_de_liquidacion(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_facturador,
    salario_base_profesor,
    salario_plus_prog,
    materia_con_plus,
):
    """Usuario con facturador=True → excluido_por_factura=True, no calcula base+plus."""
    from app.models.asignacion import Asignacion
    from app.services.liquidacion_service import LiquidacionService

    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_facturador.id,
        rol="PROFESOR",
        materia_id=materia_con_plus.id,
        cohorte_id=cohorte.id,
        comisiones=["A"],
        desde=date(2024, 3, 1),
        hasta=None,
    )
    db_session.add(asig)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_facturador,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    # Facturante: excluido, montos en 0
    assert resultado["excluido_por_factura"] is True
    assert resultado["monto_base"] == Decimal("0.00")
    assert resultado["monto_plus"] == Decimal("0.00")
    assert resultado["total"] == Decimal("0.00")


@pytest.mark.asyncio
async def test_no_facturante_incluido_en_liquidacion(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    salario_base_profesor,
):
    """Usuario con facturador=False → excluido_por_factura=False, calcula normal."""
    from app.services.liquidacion_service import LiquidacionService

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    resultado = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )

    assert resultado["excluido_por_factura"] is False
    assert resultado["monto_base"] == Decimal("1000.00")


# ============================================================================
# 6.5 — test_kpi_segmentacion
# KPIs separan general / NEXO / facturantes
# ============================================================================


@pytest.mark.asyncio
async def test_kpi_segmentacion_tres_tipos(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
    usuario_nexo,
    usuario_facturador,
    salario_base_profesor,
):
    """KPIs muestran total_general, total_nexo, total_facturantes correctamente."""
    from app.models.liquidacion import Liquidacion, EstadoLiquidacion
    from app.services.liquidacion_service import LiquidacionService

    # Liquidación normal
    liq1 = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-06",
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        comisiones=[],
        monto_base=Decimal("1000.00"),
        monto_plus=Decimal("200.00"),
        total=Decimal("1200.00"),
        es_nexo=False,
        excluido_por_factura=False,
        estado=EstadoLiquidacion.ABIERTA,
    )
    # Liquidación NEXO
    liq2 = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-06",
        usuario_id=usuario_nexo.id,
        rol="NEXO",
        comisiones=[],
        monto_base=Decimal("800.00"),
        monto_plus=Decimal("0.00"),
        total=Decimal("800.00"),
        es_nexo=True,
        excluido_por_factura=False,
        estado=EstadoLiquidacion.ABIERTA,
    )
    # Liquidación facturante (excluida)
    liq3 = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-06",
        usuario_id=usuario_facturador.id,
        rol="PROFESOR",
        comisiones=[],
        monto_base=Decimal("0.00"),
        monto_plus=Decimal("0.00"),
        total=Decimal("0.00"),
        es_nexo=False,
        excluido_por_factura=True,
        estado=EstadoLiquidacion.ABIERTA,
    )

    db_session.add_all([liq1, liq2, liq3])
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    kpis = await svc.get_kpis(periodo="2024-06", cohorte_id=cohorte.id)

    assert kpis["total_general"] == Decimal("2000.00")  # 1200 + 800
    assert kpis["total_nexo"] == Decimal("800.00")
    assert kpis["total_facturantes"] == Decimal("0.00")
    assert kpis["cantidad_liquidaciones"] == 2  # excluidos no cuentan


@pytest.mark.asyncio
async def test_kpi_sin_liquidaciones(
    db_session: AsyncSession,
    tenant,
    cohorte,
):
    """KPIs con período vacío → todos en cero."""
    from app.services.liquidacion_service import LiquidacionService

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    kpis = await svc.get_kpis(periodo="2025-01", cohorte_id=cohorte.id)

    assert kpis["total_general"] == Decimal("0.00")
    assert kpis["total_nexo"] == Decimal("0.00")
    assert kpis["total_facturantes"] == Decimal("0.00")
    assert kpis["cantidad_liquidaciones"] == 0


@pytest.mark.asyncio
async def test_kpi_solo_docentes_normales(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
):
    """KPIs con solo docentes normales: total_nexo = 0."""
    from app.models.liquidacion import Liquidacion, EstadoLiquidacion
    from app.services.liquidacion_service import LiquidacionService

    liq = Liquidacion(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2024-07",
        usuario_id=usuario_profesor.id,
        rol="PROFESOR",
        comisiones=[],
        monto_base=Decimal("1000.00"),
        monto_plus=Decimal("0.00"),
        total=Decimal("1000.00"),
        es_nexo=False,
        excluido_por_factura=False,
        estado=EstadoLiquidacion.ABIERTA,
    )
    db_session.add(liq)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    kpis = await svc.get_kpis(periodo="2024-07", cohorte_id=cohorte.id)

    assert kpis["total_general"] == Decimal("1000.00")
    assert kpis["total_nexo"] == Decimal("0.00")


# ============================================================================
# 6.6 — test_vigencia_salario
# Toma el salario vigente al período, no el último
# ============================================================================


@pytest.mark.asyncio
async def test_vigencia_salario_toma_vigente_al_periodo(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
):
    """Con dos entradas de salario, toma la vigente en el período (la más reciente <= período)."""
    from app.models.salario import SalarioBase
    from app.services.liquidacion_service import LiquidacionService

    # Salario histórico (vigente desde ene 2024)
    s1 = SalarioBase(
        tenant_id=tenant.id,
        rol="PROFESOR",
        monto=Decimal("800.00"),
        desde=date(2024, 1, 1),
        hasta=None,
    )
    # Salario más reciente (vigente desde jul 2024)
    s2 = SalarioBase(
        tenant_id=tenant.id,
        rol="PROFESOR",
        monto=Decimal("1200.00"),
        desde=date(2024, 7, 1),
        hasta=None,
    )
    db_session.add_all([s1, s2])
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)

    # Período junio 2024: s1 está vigente (800)
    resultado_junio = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-06",
    )
    assert resultado_junio["monto_base"] == Decimal("800.00")

    # Período agosto 2024: s2 está vigente (1200)
    resultado_agosto = await svc.calcular_monto(
        usuario=usuario_profesor,
        rol="PROFESOR",
        cohorte_id=cohorte.id,
        periodo="2024-08",
    )
    assert resultado_agosto["monto_base"] == Decimal("1200.00")


@pytest.mark.asyncio
async def test_vigencia_salario_ninguno_vigente_lanza_error(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
):
    """Si no hay salario vigente al período → SalarioNoEncontradoError."""
    from app.models.salario import SalarioBase
    from app.services.liquidacion_service import LiquidacionService
    from app.core.exceptions import SalarioNoEncontradoError

    # Salario solo vigente a partir de 2025
    s = SalarioBase(
        tenant_id=tenant.id,
        rol="PROFESOR",
        monto=Decimal("1000.00"),
        desde=date(2025, 1, 1),
        hasta=None,
    )
    db_session.add(s)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    with pytest.raises(SalarioNoEncontradoError):
        await svc.calcular_monto(
            usuario=usuario_profesor,
            rol="PROFESOR",
            cohorte_id=cohorte.id,
            periodo="2024-06",
        )


@pytest.mark.asyncio
async def test_vigencia_salario_con_hasta(
    db_session: AsyncSession,
    tenant,
    cohorte,
    usuario_profesor,
):
    """Salario con hasta=fecha_pasada no aplica al período actual."""
    from app.models.salario import SalarioBase
    from app.services.liquidacion_service import LiquidacionService
    from app.core.exceptions import SalarioNoEncontradoError

    # Salario vigente solo hasta marzo 2024
    s = SalarioBase(
        tenant_id=tenant.id,
        rol="PROFESOR",
        monto=Decimal("1000.00"),
        desde=date(2024, 1, 1),
        hasta=date(2024, 3, 31),
    )
    db_session.add(s)
    await db_session.flush()

    svc = LiquidacionService(db_session, tenant_id=tenant.id)
    # Período junio 2024: salario expiró en marzo
    with pytest.raises(SalarioNoEncontradoError):
        await svc.calcular_monto(
            usuario=usuario_profesor,
            rol="PROFESOR",
            cohorte_id=cohorte.id,
            periodo="2024-06",
        )
