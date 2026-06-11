"""Router de liquidaciones — C-18 liquidaciones-y-honorarios.

Endpoints:
  GET    /api/v1/liquidaciones/              — lista del período (cohorte + mes)
  POST   /api/v1/liquidaciones/calcular      — calcula y crea liquidaciones del período
  GET    /api/v1/liquidaciones/{id}          — detalle
  POST   /api/v1/liquidaciones/{id}/cerrar   — cierra (inmutable) + audit LIQUIDACION_CERRAR
  GET    /api/v1/liquidaciones/kpis          — KPIs: total_general / NEXO / facturantes

Guard: `liquidaciones:ver` (lectura) / `liquidaciones:gestionar` (escritura) — rol FINANZAS.
Flujo: Router → LiquidacionService → Repositories → Models (regla #11).
Identidad desde JWT (regla #8); nunca desde parámetros.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.exceptions import LiquidacionCerradaError, SalarioNoEncontradoError
from app.models.asignacion import Asignacion
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.models.materia import Materia
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.schemas.liquidaciones import (
    LiquidacionCalcularRequest,
    LiquidacionKPIResponse,
    LiquidacionResponse,
)
from app.services.liquidacion_service import LiquidacionService

router = APIRouter(prefix="/api/v1/liquidaciones", tags=["liquidaciones"])

_PERM_VER = Depends(require_permission("liquidaciones:ver"))
_PERM_GESTIONAR = Depends(require_permission("liquidaciones:gestionar"))


# ============================================================================
# Listado
# ============================================================================


@router.get("/", response_model=list[LiquidacionResponse])
async def list_liquidaciones(
    periodo: str = Query(..., description="Período AAAA-MM"),
    cohorte_id: UUID | None = Query(None),
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LiquidacionResponse]:
    repo = LiquidacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_por_periodo(periodo, cohorte_id=cohorte_id)
    return [LiquidacionResponse.model_validate(liq) for liq in items]


# ============================================================================
# KPIs — definido ANTES de /{id} para evitar que "kpis" sea capturado como UUID
# ============================================================================


@router.get("/kpis", response_model=LiquidacionKPIResponse)
async def get_kpis(
    periodo: str = Query(..., description="Período AAAA-MM"),
    cohorte_id: UUID = Query(...),
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LiquidacionKPIResponse:
    svc = LiquidacionService(db, tenant_id=current_user.tenant_id)
    kpis = await svc.get_kpis(periodo=periodo, cohorte_id=cohorte_id)
    return LiquidacionKPIResponse(
        periodo=periodo,
        cohorte_id=cohorte_id,
        **kpis,
    )


# ============================================================================
# Detalle
# ============================================================================


@router.get("/{id}", response_model=LiquidacionResponse)
async def get_liquidacion(
    id: UUID,
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LiquidacionResponse:
    repo = LiquidacionRepository(db, tenant_id=current_user.tenant_id)
    liq = await repo.get_by_id(id)
    if liq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liquidación no encontrada")
    return LiquidacionResponse.model_validate(liq)


# ============================================================================
# Calcular y crear liquidaciones del período
# ============================================================================


@router.post("/calcular", response_model=list[LiquidacionResponse], status_code=status.HTTP_201_CREATED)
async def calcular_liquidaciones(
    payload: LiquidacionCalcularRequest,
    request: Request,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LiquidacionResponse]:
    """Calcula y crea liquidaciones para todos los docentes activos de la cohorte/período.

    - Busca todas las asignaciones vigentes de la cohorte en el período.
    - Por cada docente-rol único, calcula el monto y crea una Liquidacion.
    - Si ya existe una liquidación para ese docente-rol-período, la sobrescribe.
    """
    from sqlalchemy import select

    svc = LiquidacionService(db, tenant_id=current_user.tenant_id)
    liq_repo = LiquidacionRepository(db, tenant_id=current_user.tenant_id)

    # Obtener docentes únicos con rol de la cohorte en el período
    from app.repositories.user_repository import UserRepository

    stmt = (
        select(Asignacion)
        .where(Asignacion.tenant_id == current_user.tenant_id)
        .where(Asignacion.deleted_at.is_(None))
        .where(Asignacion.cohorte_id == payload.cohorte_id)
    )
    result = await db.execute(stmt)
    asignaciones = list(result.scalars().all())

    # Deduplicar por (usuario_id, rol)
    docentes_vistos: set[tuple] = set()
    liquidaciones_creadas: list[Liquidacion] = []

    for asig in asignaciones:
        clave = (asig.usuario_id, asig.rol)
        if clave in docentes_vistos:
            continue
        docentes_vistos.add(clave)

        user_repo = UserRepository(db, tenant_id=current_user.tenant_id)
        usuario = await user_repo.get_by_id(asig.usuario_id)
        if usuario is None:
            continue

        try:
            resultado = await svc.calcular_monto(
                usuario=usuario,
                rol=asig.rol,
                cohorte_id=payload.cohorte_id,
                periodo=payload.periodo,
            )
        except SalarioNoEncontradoError:
            continue  # Docente sin salario configurado: se omite

        # Verificar si ya existe liquidación para este docente/período/cohorte
        liq_existente = await liq_repo.get_by_usuario_periodo(
            usuario_id=asig.usuario_id,
            periodo=payload.periodo,
            cohorte_id=payload.cohorte_id,
        )

        if liq_existente and liq_existente.estado == EstadoLiquidacion.CERRADA.value:
            continue  # No sobrescribir liquidaciones cerradas

        if liq_existente:
            liq_existente.monto_base = resultado["monto_base"]
            liq_existente.monto_plus = resultado["monto_plus"]
            liq_existente.total = resultado["total"]
            liq_existente.excluido_por_factura = resultado["excluido_por_factura"]
            liq_existente.comisiones = resultado["comisiones"]
            liq_existente.es_nexo = resultado["es_nexo"]
            liq_existente = await liq_repo.update(liq_existente)
            liquidaciones_creadas.append(liq_existente)
        else:
            nueva = Liquidacion(
                cohorte_id=payload.cohorte_id,
                periodo=payload.periodo,
                usuario_id=asig.usuario_id,
                rol=asig.rol,
                comisiones=resultado["comisiones"],
                monto_base=resultado["monto_base"],
                monto_plus=resultado["monto_plus"],
                total=resultado["total"],
                es_nexo=resultado["es_nexo"],
                excluido_por_factura=resultado["excluido_por_factura"],
                estado=EstadoLiquidacion.ABIERTA.value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            nueva = await liq_repo.create(nueva)
            liquidaciones_creadas.append(nueva)

    await db.commit()
    return [LiquidacionResponse.model_validate(liq) for liq in liquidaciones_creadas]


# ============================================================================
# Cerrar liquidación
# ============================================================================


@router.post("/{id}/cerrar", response_model=LiquidacionResponse)
async def cerrar_liquidacion(
    id: UUID,
    request: Request,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LiquidacionResponse:
    actor_id = getattr(request.state, "actor_id", current_user.id)
    svc = LiquidacionService(db, tenant_id=current_user.tenant_id)
    try:
        liq = await svc.cerrar_liquidacion(
            liquidacion_id=id,
            actor_id=actor_id,
        )
    except LiquidacionCerradaError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    await db.commit()
    return LiquidacionResponse.model_validate(liq)
