"""Router de asignaciones — vinculo usuario ↔ rol ↔ contexto académico + vigencia.

Endpoints:
  GET    /asignaciones             → lista con filtros opcionales
  POST   /asignaciones             → crear asignación (201)
  GET    /asignaciones/{id}        → obtener asignación
  PUT    /asignaciones/{id}        → actualizar asignación
  DELETE /asignaciones/{id}        → soft delete (204)

Filtros en GET: usuario_id, rol, materia_id, carrera_id, cohorte_id (todos opcionales).
Todos los endpoints requieren `equipos:asignar`.

Flujo (regla #11): Router → Repository → Models.
Identidad desde JWT (regla #8).
estado_vigencia derivado del @property del modelo — no persiste en DB.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import ASIGNACION_CREAR, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.asignaciones import AsignacionCreate, AsignacionResponse, AsignacionUpdate

router = APIRouter(prefix="/api/v1", tags=["asignaciones"])

_PERM = Depends(require_permission("equipos:asignar"))


def _to_response(a: Asignacion) -> AsignacionResponse:
    return AsignacionResponse(
        id=a.id,
        tenant_id=a.tenant_id,
        usuario_id=a.usuario_id,
        rol=a.rol,
        materia_id=a.materia_id,
        carrera_id=a.carrera_id,
        cohorte_id=a.cohorte_id,
        comisiones=a.comisiones or [],
        responsable_id=a.responsable_id,
        desde=a.desde,
        hasta=a.hasta,
        estado_vigencia=a.estado_vigencia,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.get("/asignaciones/me", response_model=list[AsignacionResponse])
async def get_mis_asignaciones(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionResponse]:
    """Asignaciones vigentes del usuario autenticado. Solo requiere estar logueado."""
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(usuario_id=current_user.id)
    return [_to_response(a) for a in items]


@router.get("/asignaciones", response_model=list[AsignacionResponse])
async def list_asignaciones(
    usuario_id: UUID | None = Query(default=None),
    rol: str | None = Query(default=None),
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionResponse]:
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        usuario_id=usuario_id,
        rol=rol,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    return [_to_response(a) for a in items]


async def _validate_cross_tenant_refs(
    payload: AsignacionCreate,
    tenant_id: UUID,
    db: AsyncSession,
) -> None:
    """Valida que los UUIDs referenciados pertenezcan al tenant del actor."""
    user_repo = UserRepository(db, tenant_id=tenant_id)
    if await user_repo.get_by_id(payload.usuario_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if payload.materia_id:
        mat_repo = MateriaRepository(db, tenant_id=tenant_id)
        if await mat_repo.get_by_id(payload.materia_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

    if payload.carrera_id:
        car_repo = CarreraRepository(db, tenant_id=tenant_id)
        if await car_repo.get_by_id(payload.carrera_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")

    if payload.cohorte_id:
        coh_repo = CohorteRepository(db, tenant_id=tenant_id)
        if await coh_repo.get_by_id(payload.cohorte_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")

    if payload.responsable_id:
        resp_repo = UserRepository(db, tenant_id=tenant_id)
        if await resp_repo.get_by_id(payload.responsable_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario responsable no encontrado",
            )


@router.post("/asignaciones", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
async def create_asignacion(
    payload: AsignacionCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponse:
    await _validate_cross_tenant_refs(payload, current_user.tenant_id, db)

    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignacion = Asignacion(
        usuario_id=payload.usuario_id,
        rol=payload.rol,
        materia_id=payload.materia_id,
        carrera_id=payload.carrera_id,
        cohorte_id=payload.cohorte_id,
        comisiones=payload.comisiones,
        responsable_id=payload.responsable_id,
        desde=payload.desde,
        hasta=payload.hasta,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    asignacion = await repo.create(asignacion)
    await db.commit()
    await db.refresh(asignacion)
    return _to_response(asignacion)


@router.get("/asignaciones/{id}", response_model=AsignacionResponse)
async def get_asignacion(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponse:
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignacion = await repo.get_by_id(id)
    if asignacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    return _to_response(asignacion)


@router.put("/asignaciones/{id}", response_model=AsignacionResponse)
async def update_asignacion(
    id: UUID,
    payload: AsignacionUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponse:
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignacion = await repo.get_by_id(id)
    if asignacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")

    campos = payload.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(asignacion, campo, valor)

    asignacion = await repo.update(asignacion)
    await db.commit()
    await db.refresh(asignacion)
    return _to_response(asignacion)


@router.delete("/asignaciones/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asignacion(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    await db.commit()
