"""Router de coloquios y evaluaciones (C-14).

Endpoints:
  POST /coloquios               → crear convocatoria (coloquios:gestionar)
  GET  /coloquios               → listar convocatorias (coloquios:gestionar)
  GET  /coloquios/metricas      → panel de métricas F7.1 (coloquios:gestionar)
  POST /coloquios/{id}/alumnos  → importar alumnos convocados F7.2 (coloquios:gestionar)
  GET  /coloquios/{id}/reservas → agenda de reservas F7.5 (coloquios:gestionar)
  POST /coloquios/{id}/reservas → reservar turno F7 ALUMNO (evaluacion:reservar)
  POST /coloquios/{id}/resultados     → registrar resultado (coloquios:gestionar)
  GET  /coloquios/{id}/resultados     → registro académico F7.5 (coloquios:gestionar)

Regla #8: identidad SIEMPRE del JWT.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.evaluacion import Evaluacion, ResultadoEvaluacion
from app.repositories.evaluacion_repository import (
    EvaluacionRepository,
    ReservaEvaluacionRepository,
    ResultadoEvaluacionRepository,
)
from app.schemas.coloquios import (
    AlumnosImportPayload,
    EvaluacionCreate,
    EvaluacionResponse,
    MetricasColoquioResponse,
    ResultadoCreate,
    ResultadoResponse,
    ReservaCreate,
    ReservaResponse,
)
from app.services.coloquio_service import ColoquioService

router = APIRouter(prefix="/api/v1/coloquios", tags=["coloquios"])

_PERM_GESTIONAR = Depends(require_permission("coloquios:gestionar"))
_PERM_RESERVAR = Depends(require_permission("evaluacion:reservar"))


def _ev_to_response(ev: Evaluacion) -> EvaluacionResponse:
    return EvaluacionResponse(
        id=ev.id,
        tenant_id=ev.tenant_id,
        materia_id=ev.materia_id,
        cohorte_id=ev.cohorte_id,
        tipo=ev.tipo,
        instancia=ev.instancia,
        dias_disponibles=ev.dias_disponibles,
        cupos_por_dia=ev.cupos_por_dia,
    )


# ---------------------------------------------------------------------------
# Métricas — ANTES de /{id} para evitar conflictos de ruta
# ---------------------------------------------------------------------------


@router.get("/metricas", response_model=MetricasColoquioResponse)
async def panel_metricas(
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricasColoquioResponse:
    """Panel de métricas de coloquios del tenant (F7.1)."""
    return await ColoquioService.get_metricas(db, tenant_id=current_user.tenant_id)


# ---------------------------------------------------------------------------
# POST /coloquios — crear convocatoria (F7.3)
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EvaluacionResponse)
async def crear_evaluacion(
    payload: EvaluacionCreate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResponse:
    """Crea una nueva convocatoria de evaluación."""
    ev = Evaluacion(
        materia_id=payload.materia_id,
        cohorte_id=payload.cohorte_id,
        tipo=payload.tipo,
        instancia=payload.instancia,
        dias_disponibles=payload.dias_disponibles,
        cupos_por_dia=payload.cupos_por_dia,
    )
    repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    ev = await repo.create(ev)
    await db.commit()
    await db.refresh(ev)
    return _ev_to_response(ev)


# ---------------------------------------------------------------------------
# GET /coloquios — listar convocatorias (F7.4)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[EvaluacionResponse])
async def listar_evaluaciones(
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EvaluacionResponse]:
    """Lista convocatorias activas del tenant."""
    repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list()
    return [_ev_to_response(ev) for ev in items]


# ---------------------------------------------------------------------------
# POST /coloquios/{id}/alumnos — importar alumnos convocados (F7.2)
# ---------------------------------------------------------------------------


@router.post("/{evaluacion_id}/alumnos", status_code=status.HTTP_201_CREATED)
async def importar_alumnos(
    evaluacion_id: UUID,
    payload: AlumnosImportPayload,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Carga padrón de alumnos habilitados para la convocatoria (crea ResultadoEvaluacion stubs)."""
    eval_repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    ev = await eval_repo.get_by_id(evaluacion_id)
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")

    resultado_repo = ResultadoEvaluacionRepository(db, tenant_id=current_user.tenant_id)
    creados = 0
    for alumno_id in payload.alumno_ids:
        existente = await resultado_repo.get_by_alumno_evaluacion(
            alumno_id=alumno_id, evaluacion_id=evaluacion_id
        )
        if existente is None:
            r = ResultadoEvaluacion(evaluacion_id=evaluacion_id, alumno_id=alumno_id, nota_final=None)
            await resultado_repo.create(r)
            creados += 1

    await db.commit()
    return {"importados": creados, "total_enviados": len(payload.alumno_ids)}


# ---------------------------------------------------------------------------
# GET /coloquios/{id}/reservas — agenda de reservas activas (F7.5)
# ---------------------------------------------------------------------------


@router.get("/{evaluacion_id}/reservas", response_model=list[ReservaResponse])
async def listar_reservas(
    evaluacion_id: UUID,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReservaResponse]:
    """Lista reservas activas de una convocatoria."""
    eval_repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    if await eval_repo.get_by_id(evaluacion_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")

    repo = ReservaEvaluacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_by_evaluacion(evaluacion_id)
    return [
        ReservaResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            evaluacion_id=r.evaluacion_id,
            alumno_id=r.alumno_id,
            fecha_hora=r.fecha_hora,
            estado=r.estado,
        )
        for r in items
    ]


# ---------------------------------------------------------------------------
# POST /coloquios/{id}/reservas — reservar turno (ALUMNO, F7)
# ---------------------------------------------------------------------------


@router.post("/{evaluacion_id}/reservas", status_code=status.HTTP_201_CREATED, response_model=ReservaResponse)
async def reservar_turno(
    evaluacion_id: UUID,
    payload: ReservaCreate,
    _: None = _PERM_RESERVAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReservaResponse:
    """ALUMNO reserva un turno en una convocatoria."""
    reserva = await ColoquioService.reservar_turno(
        evaluacion_id=evaluacion_id,
        alumno_id=current_user.id,
        fecha_hora=payload.fecha_hora,
        session=db,
        tenant_id=current_user.tenant_id,
    )
    await db.commit()
    await db.refresh(reserva)
    return ReservaResponse(
        id=reserva.id,
        tenant_id=reserva.tenant_id,
        evaluacion_id=reserva.evaluacion_id,
        alumno_id=reserva.alumno_id,
        fecha_hora=reserva.fecha_hora,
        estado=reserva.estado,
    )


# ---------------------------------------------------------------------------
# POST /coloquios/{id}/resultados — registrar nota final (F7.5)
# ---------------------------------------------------------------------------


@router.post("/{evaluacion_id}/resultados", status_code=status.HTTP_201_CREATED, response_model=ResultadoResponse)
async def registrar_resultado(
    evaluacion_id: UUID,
    payload: ResultadoCreate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResultadoResponse:
    """Registra o actualiza la nota final de un alumno en una convocatoria."""
    eval_repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    if await eval_repo.get_by_id(evaluacion_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")

    resultado_repo = ResultadoEvaluacionRepository(db, tenant_id=current_user.tenant_id)
    existente = await resultado_repo.get_by_alumno_evaluacion(
        alumno_id=payload.alumno_id, evaluacion_id=evaluacion_id
    )
    if existente is not None:
        existente.nota_final = payload.nota_final
        r = await resultado_repo.update(existente)
    else:
        r = ResultadoEvaluacion(
            evaluacion_id=evaluacion_id,
            alumno_id=payload.alumno_id,
            nota_final=payload.nota_final,
        )
        r = await resultado_repo.create(r)

    await db.commit()
    await db.refresh(r)
    return ResultadoResponse(
        id=r.id,
        tenant_id=r.tenant_id,
        evaluacion_id=r.evaluacion_id,
        alumno_id=r.alumno_id,
        nota_final=r.nota_final,
    )


# ---------------------------------------------------------------------------
# GET /coloquios/{id}/resultados — registro académico (F7.5)
# ---------------------------------------------------------------------------


@router.get("/{evaluacion_id}/resultados", response_model=list[ResultadoResponse])
async def listar_resultados(
    evaluacion_id: UUID,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResultadoResponse]:
    """Registro académico consolidado: notas finales de una convocatoria."""
    eval_repo = EvaluacionRepository(db, tenant_id=current_user.tenant_id)
    if await eval_repo.get_by_id(evaluacion_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")

    resultado_repo = ResultadoEvaluacionRepository(db, tenant_id=current_user.tenant_id)
    items = await resultado_repo.list_by_evaluacion(evaluacion_id)
    return [
        ResultadoResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            evaluacion_id=r.evaluacion_id,
            alumno_id=r.alumno_id,
            nota_final=r.nota_final,
        )
        for r in items
    ]
