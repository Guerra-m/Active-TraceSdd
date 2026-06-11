"""Router de programas de materia y fechas académicas (C-17).

Endpoints:
  POST   /programas                → asociar programa (estructura:gestionar)
  GET    /programas                → listar programas del tenant (estructura:gestionar)
  DELETE /programas/{id}           → soft delete (estructura:gestionar)

  POST   /fechas-academicas        → crear fecha (estructura:gestionar)
  GET    /fechas-academicas        → listar fechas con filtros (estructura:gestionar)
  PATCH  /fechas-academicas/{id}   → editar fecha o titulo (estructura:gestionar)
  DELETE /fechas-academicas/{id}   → soft delete (estructura:gestionar)

Regla #8: identidad SIEMPRE del JWT.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.programa_materia import FechaAcademica, ProgramaMateria
from app.repositories.programa_repository import FechaAcademicaRepository, ProgramaMateriaRepository
from app.schemas.programas import (
    FechaAcademicaCreate,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
    ProgramaMateriaCreate,
    ProgramaMateriaResponse,
)

router = APIRouter(tags=["programas-academicos"])

_PERM = Depends(require_permission("estructura:gestionar"))


def _fecha_to_response(f: FechaAcademica) -> FechaAcademicaResponse:
    return FechaAcademicaResponse(
        id=f.id,
        tenant_id=f.tenant_id,
        materia_id=f.materia_id,
        cohorte_id=f.cohorte_id,
        tipo=f.tipo,
        numero=f.numero,
        periodo=f.periodo,
        fecha=f.fecha,
        titulo=f.titulo,
    )


def _programa_to_response(p: ProgramaMateria) -> ProgramaMateriaResponse:
    return ProgramaMateriaResponse(
        id=p.id,
        tenant_id=p.tenant_id,
        materia_id=p.materia_id,
        carrera_id=p.carrera_id,
        cohorte_id=p.cohorte_id,
        titulo=p.titulo,
        referencia_archivo=p.referencia_archivo,
        cargado_at=p.cargado_at,
    )


# ---------------------------------------------------------------------------
# Programas de materia
# ---------------------------------------------------------------------------

programas_router = APIRouter(prefix="/api/v1/programas")


@programas_router.post("", status_code=status.HTTP_201_CREATED, response_model=ProgramaMateriaResponse)
async def crear_programa(
    payload: ProgramaMateriaCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramaMateriaResponse:
    p = ProgramaMateria(
        materia_id=payload.materia_id,
        carrera_id=payload.carrera_id,
        cohorte_id=payload.cohorte_id,
        titulo=payload.titulo,
        referencia_archivo=payload.referencia_archivo,
        cargado_at=datetime.now(timezone.utc),
    )
    repo = ProgramaMateriaRepository(db, tenant_id=current_user.tenant_id)
    p = await repo.create(p)
    await db.commit()
    await db.refresh(p)
    return _programa_to_response(p)


@programas_router.get("", response_model=list[ProgramaMateriaResponse])
async def listar_programas(
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgramaMateriaResponse]:
    repo = ProgramaMateriaRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id)
    return [_programa_to_response(p) for p in items]


@programas_router.delete("/{programa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_programa(
    programa_id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = ProgramaMateriaRepository(db, tenant_id=current_user.tenant_id)
    ok = await repo.soft_delete(programa_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programa no encontrado")
    await db.commit()


# ---------------------------------------------------------------------------
# Fechas académicas
# ---------------------------------------------------------------------------

fechas_router = APIRouter(prefix="/api/v1/fechas-academicas")


@fechas_router.post("", status_code=status.HTTP_201_CREATED, response_model=FechaAcademicaResponse)
async def crear_fecha(
    payload: FechaAcademicaCreate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FechaAcademicaResponse:
    f = FechaAcademica(
        materia_id=payload.materia_id,
        cohorte_id=payload.cohorte_id,
        tipo=payload.tipo,
        numero=payload.numero,
        periodo=payload.periodo,
        fecha=payload.fecha,
        titulo=payload.titulo,
    )
    repo = FechaAcademicaRepository(db, tenant_id=current_user.tenant_id)
    f = await repo.create(f)
    await db.commit()
    await db.refresh(f)
    return _fecha_to_response(f)


@fechas_router.get("", response_model=list[FechaAcademicaResponse])
async def listar_fechas(
    materia_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    periodo: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FechaAcademicaResponse]:
    repo = FechaAcademicaRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(materia_id=materia_id, cohorte_id=cohorte_id, periodo=periodo, tipo=tipo)
    return [_fecha_to_response(f) for f in items]


@fechas_router.patch("/{fecha_id}", response_model=FechaAcademicaResponse)
async def editar_fecha(
    fecha_id: UUID,
    payload: FechaAcademicaUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FechaAcademicaResponse:
    repo = FechaAcademicaRepository(db, tenant_id=current_user.tenant_id)
    f = await repo.get_by_id(fecha_id)
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")
    if payload.fecha is not None:
        f.fecha = payload.fecha
    if payload.titulo is not None:
        f.titulo = payload.titulo
    f = await repo.update(f)
    await db.commit()
    await db.refresh(f)
    return _fecha_to_response(f)


@fechas_router.delete("/{fecha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_fecha(
    fecha_id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = FechaAcademicaRepository(db, tenant_id=current_user.tenant_id)
    ok = await repo.soft_delete(fecha_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fecha académica no encontrada")
    await db.commit()
