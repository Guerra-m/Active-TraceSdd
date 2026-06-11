"""Router de estructura académica — ABM de Carrera, Cohorte y Materia.

Endpoints:
  GET    /admin/carreras                  → lista carreras del tenant
  POST   /admin/carreras                  → crear carrera
  GET    /admin/carreras/{id}             → obtener carrera
  PUT    /admin/carreras/{id}             → actualizar carrera
  PATCH  /admin/carreras/{id}/estado      → cambiar estado (Activa/Inactiva)
  DELETE /admin/carreras/{id}             → soft delete

  GET    /admin/cohortes                  → lista cohortes del tenant
  POST   /admin/cohortes                  → crear cohorte (requiere carrera Activa)
  GET    /admin/cohortes/{id}             → obtener cohorte
  DELETE /admin/cohortes/{id}             → soft delete

  GET    /admin/materias                  → lista materias del tenant
  POST   /admin/materias                  → crear materia
  GET    /admin/materias/{id}             → obtener materia
  PUT    /admin/materias/{id}             → actualizar materia
  PATCH  /admin/materias/{id}/estado      → cambiar estado (Activa/Inactiva)
  DELETE /admin/materias/{id}             → soft delete

Todos los endpoints requieren permiso `estructura:gestionar` (ADMIN).
Flujo (regla #11): Router → Repository → Models.
Identidad desde JWT (regla #8); nunca desde parámetros de petición.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository
from app.schemas.estructura import (
    CarreraCreate,
    CarreraEstadoUpdate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteResponse,
    MateriaCreate,
    MateriaEstadoUpdate,
    MateriaResponse,
    MateriaUpdate,
)

router = APIRouter(prefix="/api/v1/admin", tags=["estructura-academica"])

_PERM = Depends(require_permission("estructura:gestionar"))

# ============================================================================
# CARRERAS
# ============================================================================


@router.get("/carreras", response_model=list[CarreraResponse])
async def list_carreras(
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CarreraResponse]:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list()
    return [CarreraResponse.model_validate(c) for c in items]


@router.post("/carreras", response_model=CarreraResponse, status_code=status.HTTP_201_CREATED)
async def create_carrera(
    payload: CarreraCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    carrera = Carrera(
        codigo=payload.codigo,
        nombre=payload.nombre,
        estado="Activa",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    try:
        carrera = await repo.create(carrera)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Código de carrera ya existe en este tenant",
        )
    return CarreraResponse.model_validate(carrera)


@router.get("/carreras/{id}", response_model=CarreraResponse)
async def get_carrera(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    carrera = await repo.get_by_id(id)
    if carrera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
    return CarreraResponse.model_validate(carrera)


@router.put("/carreras/{id}", response_model=CarreraResponse)
async def update_carrera(
    id: UUID,
    payload: CarreraUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    carrera = await repo.get_by_id(id)
    if carrera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
    carrera.codigo = payload.codigo
    carrera.nombre = payload.nombre
    try:
        carrera = await repo.update(carrera)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Código de carrera ya existe en este tenant",
        )
    return CarreraResponse.model_validate(carrera)


@router.patch("/carreras/{id}/estado", response_model=CarreraResponse)
async def patch_carrera_estado(
    id: UUID,
    payload: CarreraEstadoUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    carrera = await repo.update_estado(id, payload.estado)
    if carrera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
    await db.commit()
    return CarreraResponse.model_validate(carrera)


@router.delete("/carreras/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carrera(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
    await db.commit()


# ============================================================================
# COHORTES
# ============================================================================


@router.get("/cohortes", response_model=list[CohorteResponse])
async def list_cohortes(
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CohorteResponse]:
    repo = CohorteRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list()
    return [CohorteResponse.model_validate(c) for c in items]


@router.post("/cohortes", response_model=CohorteResponse, status_code=status.HTTP_201_CREATED)
async def create_cohorte(
    payload: CohorteCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    carrera_repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    carrera = await carrera_repo.get_by_id(payload.carrera_id)
    if carrera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
    if carrera.estado == "Inactiva":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pueden crear cohortes para una carrera inactiva",
        )

    repo = CohorteRepository(db, tenant_id=current_user.tenant_id)
    cohorte = Cohorte(
        carrera_id=payload.carrera_id,
        nombre=payload.nombre,
        anio=payload.anio,
        vig_desde=payload.vig_desde,
        vig_hasta=payload.vig_hasta,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    try:
        cohorte = await repo.create(cohorte)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nombre de cohorte ya existe para esta carrera en este tenant",
        )
    return CohorteResponse.model_validate(cohorte)


@router.get("/cohortes/{id}", response_model=CohorteResponse)
async def get_cohorte(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    repo = CohorteRepository(db, tenant_id=current_user.tenant_id)
    cohorte = await repo.get_by_id(id)
    if cohorte is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")
    return CohorteResponse.model_validate(cohorte)


@router.delete("/cohortes/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohorte(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = CohorteRepository(db, tenant_id=current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")
    await db.commit()


# ============================================================================
# MATERIAS
# ============================================================================


@router.get("/materias", response_model=list[MateriaResponse])
async def list_materias(
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MateriaResponse]:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list()
    return [MateriaResponse.model_validate(m) for m in items]


@router.post("/materias", response_model=MateriaResponse, status_code=status.HTTP_201_CREATED)
async def create_materia(
    payload: MateriaCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    materia = Materia(
        codigo=payload.codigo,
        nombre=payload.nombre,
        estado="Activa",
        grupo_plus=payload.grupo_plus,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    try:
        materia = await repo.create(materia)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Código de materia ya existe en este tenant",
        )
    return MateriaResponse.model_validate(materia)


@router.get("/materias/{id}", response_model=MateriaResponse)
async def get_materia(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    materia = await repo.get_by_id(id)
    if materia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    return MateriaResponse.model_validate(materia)


@router.put("/materias/{id}", response_model=MateriaResponse)
async def update_materia(
    id: UUID,
    payload: MateriaUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    materia = await repo.get_by_id(id)
    if materia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    materia.codigo = payload.codigo
    materia.nombre = payload.nombre
    materia.grupo_plus = payload.grupo_plus
    try:
        materia = await repo.update(materia)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Código de materia ya existe en este tenant",
        )
    return MateriaResponse.model_validate(materia)


@router.patch("/materias/{id}/estado", response_model=MateriaResponse)
async def patch_materia_estado(
    id: UUID,
    payload: MateriaEstadoUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    materia = await repo.update_estado(id, payload.estado)
    if materia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    await db.commit()
    return MateriaResponse.model_validate(materia)


@router.delete("/materias/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_materia(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    await db.commit()
