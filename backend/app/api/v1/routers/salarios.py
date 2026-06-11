"""Router de salarios (base y plus) — C-18 liquidaciones-y-honorarios.

Endpoints:
  GET    /api/v1/liquidaciones/salarios/base         — lista salarios base
  POST   /api/v1/liquidaciones/salarios/base         — crear entrada
  PUT    /api/v1/liquidaciones/salarios/base/{id}    — editar
  GET    /api/v1/liquidaciones/salarios/plus         — lista salarios plus
  POST   /api/v1/liquidaciones/salarios/plus         — crear entrada
  PUT    /api/v1/liquidaciones/salarios/plus/{id}    — editar

Guard: `liquidaciones:gestionar` (FINANZAS).
Flujo: Router → Repository (sin Service: operaciones CRUD simples).
Identidad desde JWT (regla #8); nunca desde parámetros.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.salario import SalarioBase, SalarioPlus
from app.repositories.salario_repository import SalarioRepository
from app.schemas.liquidaciones import (
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)

router = APIRouter(prefix="/api/v1/liquidaciones/salarios", tags=["salarios"])

_PERM_GESTIONAR = Depends(require_permission("liquidaciones:gestionar"))
_PERM_VER = Depends(require_permission("liquidaciones:ver"))


# ============================================================================
# SALARIO BASE
# ============================================================================


@router.get("/base", response_model=list[SalarioBaseResponse])
async def list_salarios_base(
    rol: str | None = None,
    solo_vigentes: bool = False,
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SalarioBaseResponse]:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_base(rol=rol, solo_vigentes=solo_vigentes)
    return [SalarioBaseResponse.model_validate(s) for s in items]


@router.post("/base", response_model=SalarioBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_salario_base(
    payload: SalarioBaseCreate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioBaseResponse:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    obj = SalarioBase(
        rol=payload.rol,
        monto=payload.monto,
        desde=payload.desde,
        hasta=payload.hasta,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    obj = await repo.create_base(obj)
    await db.commit()
    return SalarioBaseResponse.model_validate(obj)


@router.put("/base/{id}", response_model=SalarioBaseResponse)
async def update_salario_base(
    id: UUID,
    payload: SalarioBaseUpdate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioBaseResponse:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    obj = await repo.get_base_by_id(id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SalarioBase no encontrado")
    obj.rol = payload.rol
    obj.monto = payload.monto
    obj.desde = payload.desde
    obj.hasta = payload.hasta
    obj = await repo.update_base(obj)
    await db.commit()
    return SalarioBaseResponse.model_validate(obj)


# ============================================================================
# SALARIO PLUS
# ============================================================================


@router.get("/plus", response_model=list[SalarioPlusResponse])
async def list_salarios_plus(
    grupo: str | None = None,
    rol: str | None = None,
    solo_vigentes: bool = False,
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SalarioPlusResponse]:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_plus(grupo=grupo, rol=rol, solo_vigentes=solo_vigentes)
    return [SalarioPlusResponse.model_validate(s) for s in items]


@router.post("/plus", response_model=SalarioPlusResponse, status_code=status.HTTP_201_CREATED)
async def create_salario_plus(
    payload: SalarioPlusCreate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioPlusResponse:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    obj = SalarioPlus(
        grupo=payload.grupo,
        rol=payload.rol,
        descripcion=payload.descripcion,
        monto=payload.monto,
        desde=payload.desde,
        hasta=payload.hasta,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    obj = await repo.create_plus(obj)
    await db.commit()
    return SalarioPlusResponse.model_validate(obj)


@router.put("/plus/{id}", response_model=SalarioPlusResponse)
async def update_salario_plus(
    id: UUID,
    payload: SalarioPlusUpdate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioPlusResponse:
    repo = SalarioRepository(db, tenant_id=current_user.tenant_id)
    obj = await repo.get_plus_by_id(id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SalarioPlus no encontrado")
    obj.grupo = payload.grupo
    obj.rol = payload.rol
    obj.descripcion = payload.descripcion
    obj.monto = payload.monto
    obj.desde = payload.desde
    obj.hasta = payload.hasta
    obj = await repo.update_plus(obj)
    await db.commit()
    return SalarioPlusResponse.model_validate(obj)
