"""Router de análisis académico — C-11 analisis-atrasados-reportes.

Endpoints (todos GET — solo lectura):
  GET /analisis/atrasados/{asignacion_id}/{materia_id}   → alumnos atrasados (RN-06)
  GET /analisis/ranking/{asignacion_id}/{materia_id}     → ranking aprobadas (RN-09)
  GET /analisis/notas-finales/{asignacion_id}/{materia_id} → nota final por alumno (F2.5)

PROFESOR con is_own_resource: solo sus propias asignaciones.
COORDINADOR/ADMIN: acceso global dentro del tenant.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.analisis import (
    AtrasadosResponse,
    EntregasSinCorregirResponse,
    MonitorResponse,
    NotasFinalesResponse,
    RankingResponse,
)
from app.services.analisis_service import (
    get_atrasados,
    get_entregas_sin_corregir,
    get_monitor,
    get_notas_finales,
    get_ranking,
)

router = APIRouter(prefix="/api/v1", tags=["analisis"])

_PERM = Depends(require_permission("atrasados:ver"))


async def _check_asignacion_scope(
    asignacion_id: UUID,
    current_user,
    request: Request,
    db: AsyncSession,
) -> None:
    """Verifica que el actor sea el titular de la asignación (si is_own_resource)."""
    is_own = getattr(request.state, "permission_is_own_resource", False)
    if not is_own:
        return
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignacion = await repo.get_by_id(asignacion_id)
    if asignacion is None or asignacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin acceso a esta asignación",
        )


@router.get(
    "/analisis/atrasados/{asignacion_id}/{materia_id}",
    response_model=AtrasadosResponse,
)
async def get_atrasados_endpoint(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AtrasadosResponse:
    """Lista alumnos atrasados: con actividades faltantes o notas reprobadas (RN-06).

    Requiere permiso: `atrasados:ver`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    alumnos = await get_atrasados(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    return AtrasadosResponse(total_atrasados=len(alumnos), alumnos=alumnos)


@router.get(
    "/analisis/ranking/{asignacion_id}/{materia_id}",
    response_model=RankingResponse,
)
async def get_ranking_endpoint(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RankingResponse:
    """Ranking de alumnos por cantidad de actividades aprobadas (RN-09).

    Excluye alumnos sin ninguna aprobada.
    Requiere permiso: `atrasados:ver`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    ranking = await get_ranking(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    return RankingResponse(total_alumnos=len(ranking), ranking=ranking)


@router.get(
    "/analisis/notas-finales/{asignacion_id}/{materia_id}",
    response_model=NotasFinalesResponse,
)
async def get_notas_finales_endpoint(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotasFinalesResponse:
    """Nota final promedio por alumno (F2.5).

    Promedia solo calificaciones numéricas. Incluye todos los alumnos con
    al menos una calificación registrada en el padrón.
    Requiere permiso: `atrasados:ver`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    alumnos = await get_notas_finales(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    return NotasFinalesResponse(total_alumnos=len(alumnos), alumnos=alumnos)


@router.get(
    "/analisis/entregas-sin-corregir/{asignacion_id}/{materia_id}",
    response_model=EntregasSinCorregirResponse,
)
async def get_entregas_sin_corregir_endpoint(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntregasSinCorregirResponse:
    """Calificaciones importadas sin nota (pendientes de corrección).

    Requiere permiso: `atrasados:ver`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    items = await get_entregas_sin_corregir(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    return EntregasSinCorregirResponse(total=len(items), items=items)


@router.get(
    "/analisis/monitor/{asignacion_id}/{materia_id}",
    response_model=MonitorResponse,
)
async def get_monitor_endpoint(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonitorResponse:
    """Métricas de seguimiento: totales, atrasados, promedio, comunicaciones.

    Requiere permiso: `atrasados:ver`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    data = await get_monitor(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    return MonitorResponse(**data)
