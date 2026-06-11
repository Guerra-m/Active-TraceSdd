"""Router de tareas internas (C-16).

Endpoints:
  POST   /tareas              → crear tarea (tareas:gestionar)
  GET    /tareas              → listar (PROF: propias; COORD/ADMIN: todas del tenant)
  GET    /tareas/{id}         → detalle
  PATCH  /tareas/{id}         → cambiar estado/descripcion
  POST   /tareas/{id}/comentarios → agregar comentario al hilo
  GET    /tareas/{id}/comentarios → ver hilo de comentarios

D-04: scope resuelto por is_own_resource del permiso.
Regla #8: identidad SIEMPRE del JWT.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.tarea_repository import ComentarioTareaRepository, TareaRepository
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCreate,
    TareaResponse,
    TareaUpdate,
)

router = APIRouter(prefix="/api/v1/tareas", tags=["tareas"])

_PERM = Depends(require_permission("tareas:gestionar"))


def _tarea_to_response(t: Tarea) -> TareaResponse:
    return TareaResponse(
        id=t.id,
        tenant_id=t.tenant_id,
        materia_id=t.materia_id,
        asignado_a=t.asignado_a,
        asignado_por=t.asignado_por,
        estado=t.estado,
        descripcion=t.descripcion,
        contexto_id=t.contexto_id,
        created_at=t.created_at,
    )


def _comentario_to_response(c: ComentarioTarea) -> ComentarioResponse:
    return ComentarioResponse(
        id=c.id,
        tarea_id=c.tarea_id,
        autor_id=c.autor_id,
        texto=c.texto,
        created_at=c.created_at,
    )


# ---------------------------------------------------------------------------
# POST /tareas — crear tarea
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TareaResponse)
async def crear_tarea(
    payload: TareaCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    tarea = Tarea(
        materia_id=payload.materia_id,
        asignado_a=payload.asignado_a,
        asignado_por=current_user.id,
        estado="Pendiente",
        descripcion=payload.descripcion,
        contexto_id=payload.contexto_id,
    )
    repo = TareaRepository(db, tenant_id=current_user.tenant_id)
    tarea = await repo.create(tarea)
    await db.commit()
    await db.refresh(tarea)
    return _tarea_to_response(tarea)


# ---------------------------------------------------------------------------
# GET /tareas — listar (scope por is_own_resource)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TareaResponse])
async def listar_tareas(
    request: Request,
    estado: str | None = Query(default=None),
    materia_id: UUID | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TareaResponse]:
    """Lista tareas. PROFESOR/TUTOR: solo las asignadas a ellos. COORD/ADMIN: todas del tenant."""
    is_own = getattr(request.state, "permission_is_own_resource", True)
    repo = TareaRepository(db, tenant_id=current_user.tenant_id)

    asignado_a = current_user.id if is_own else None
    items = await repo.list_filtrado(
        asignado_a=asignado_a,
        estado=estado,
        materia_id=materia_id,
    )
    return [_tarea_to_response(t) for t in items]


# ---------------------------------------------------------------------------
# GET /tareas/{id} — detalle
# ---------------------------------------------------------------------------


@router.get("/{tarea_id}", response_model=TareaResponse)
async def detalle_tarea(
    tarea_id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    repo = TareaRepository(db, tenant_id=current_user.tenant_id)
    tarea = await repo.get_by_id(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return _tarea_to_response(tarea)


# ---------------------------------------------------------------------------
# PATCH /tareas/{id} — cambiar estado o descripcion
# ---------------------------------------------------------------------------


@router.patch("/{tarea_id}", response_model=TareaResponse)
async def actualizar_tarea(
    tarea_id: UUID,
    payload: TareaUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    repo = TareaRepository(db, tenant_id=current_user.tenant_id)
    tarea = await repo.get_by_id(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    if payload.estado is not None:
        tarea.estado = payload.estado
    if payload.descripcion is not None:
        tarea.descripcion = payload.descripcion

    tarea = await repo.update(tarea)
    await db.commit()
    await db.refresh(tarea)
    return _tarea_to_response(tarea)


# ---------------------------------------------------------------------------
# POST /tareas/{id}/comentarios — agregar comentario
# ---------------------------------------------------------------------------


@router.post("/{tarea_id}/comentarios", status_code=status.HTTP_201_CREATED, response_model=ComentarioResponse)
async def agregar_comentario(
    tarea_id: UUID,
    payload: ComentarioCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComentarioResponse:
    tarea_repo = TareaRepository(db, tenant_id=current_user.tenant_id)
    if await tarea_repo.get_by_id(tarea_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    comentario = ComentarioTarea(
        tarea_id=tarea_id,
        autor_id=current_user.id,
        texto=payload.texto,
    )
    repo = ComentarioTareaRepository(db, tenant_id=current_user.tenant_id)
    comentario = await repo.create(comentario)
    await db.commit()
    await db.refresh(comentario)
    return _comentario_to_response(comentario)


# ---------------------------------------------------------------------------
# GET /tareas/{id}/comentarios — hilo de comentarios
# ---------------------------------------------------------------------------


@router.get("/{tarea_id}/comentarios", response_model=list[ComentarioResponse])
async def listar_comentarios(
    tarea_id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComentarioResponse]:
    tarea_repo = TareaRepository(db, tenant_id=current_user.tenant_id)
    if await tarea_repo.get_by_id(tarea_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    repo = ComentarioTareaRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_by_tarea(tarea_id)
    return [_comentario_to_response(c) for c in items]
