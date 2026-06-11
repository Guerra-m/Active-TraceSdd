"""Router de facturas — C-18 liquidaciones-y-honorarios.

Endpoints:
  GET    /api/v1/facturas/         — listar facturas (filtro: docente, período, estado)
  POST   /api/v1/facturas/         — registrar factura
  PUT    /api/v1/facturas/{id}/abonar  — marcar como abonada

Guard: `liquidaciones:ver` (lectura) / `liquidaciones:gestionar` (escritura) — rol FINANZAS.
Flujo: Router → Repository (CRUD simple, sin Service).
Identidad desde JWT (regla #8); nunca desde parámetros.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.factura import EstadoFactura, Factura
from app.repositories.factura_repository import FacturaRepository
from app.schemas.liquidaciones import (
    FacturaAbonarRequest,
    FacturaCreate,
    FacturaResponse,
)

router = APIRouter(prefix="/api/v1/facturas", tags=["facturas"])

_PERM_VER = Depends(require_permission("liquidaciones:ver"))
_PERM_GESTIONAR = Depends(require_permission("liquidaciones:gestionar"))


@router.get("/", response_model=list[FacturaResponse])
async def list_facturas(
    usuario_id: UUID | None = Query(None),
    periodo: str | None = Query(None),
    estado: str | None = Query(None),
    _: None = _PERM_VER,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FacturaResponse]:
    repo = FacturaRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_facturas(
        usuario_id=usuario_id,
        periodo=periodo,
        estado=estado,
    )
    return [FacturaResponse.model_validate(f) for f in items]


@router.post("/", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
async def create_factura(
    payload: FacturaCreate,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaResponse:
    repo = FacturaRepository(db, tenant_id=current_user.tenant_id)
    now = datetime.now(timezone.utc)
    obj = Factura(
        usuario_id=payload.usuario_id,
        periodo=payload.periodo,
        monto=payload.monto,
        detalle=payload.detalle,
        archivo_ref=payload.archivo_ref,
        estado=EstadoFactura.PENDIENTE.value,
        fecha_carga=now,
        fecha_pago=None,
        created_at=now,
        updated_at=now,
    )
    obj = await repo.create(obj)
    await db.commit()
    return FacturaResponse.model_validate(obj)


@router.put("/{id}/abonar", response_model=FacturaResponse)
async def abonar_factura(
    id: UUID,
    payload: FacturaAbonarRequest,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaResponse:
    repo = FacturaRepository(db, tenant_id=current_user.tenant_id)
    obj = await repo.get_by_id(id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    if obj.estado == EstadoFactura.ABONADA.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La factura ya está abonada",
        )
    obj.estado = EstadoFactura.ABONADA.value
    obj.fecha_pago = payload.fecha_pago
    obj = await repo.update(obj)
    await db.commit()
    return FacturaResponse.model_validate(obj)
