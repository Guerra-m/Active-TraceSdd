"""Router de comunicaciones — C-12 comunicaciones-cola-worker.

Endpoints:
  POST   /comunicaciones/preview               → preview sin persistir (RN-16)
  POST   /comunicaciones/lotes                 → crear lote de envío masivo
  POST   /comunicaciones/lotes/{id}/aprobar    → aprobar lote (comunicacion:aprobar)
  DELETE /comunicaciones/lotes/{id}            → cancelar lote
  GET    /comunicaciones/lotes                 → listar lotes del tenant

Permiso base: `comunicacion:enviar` (PROFESOR/COORDINADOR/ADMIN).
Aprobación:   `comunicacion:aprobar` (COORDINADOR/ADMIN).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import COMUNICACION_ENVIAR, audit
from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db, require_permission
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicaciones import (
    CrearLoteRequest,
    LoteComunicacionResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.services.comunicacion_service import (
    aprobar_lote,
    cancelar_lote,
    crear_lote,
    render_preview,
)

router = APIRouter(prefix="/api/v1", tags=["comunicaciones"])

_PERM_ENVIAR = Depends(require_permission("comunicacion:enviar"))
_PERM_APROBAR = Depends(require_permission("comunicacion:aprobar"))


@router.post(
    "/comunicaciones/preview",
    response_model=PreviewResponse,
)
async def preview_comunicacion(
    payload: PreviewRequest,
    _: None = _PERM_ENVIAR,
) -> PreviewResponse:
    """Retorna el asunto y cuerpo renderizados con las variables de ejemplo (RN-16).

    No persiste nada. Usar antes de confirmar el envío.
    """
    asunto, cuerpo = render_preview(
        payload.asunto_template,
        payload.cuerpo_template,
        payload.variables_ejemplo,
    )
    return PreviewResponse(asunto_renderizado=asunto, cuerpo_renderizado=cuerpo)


@router.post(
    "/comunicaciones/lotes",
    response_model=LoteComunicacionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_lote_endpoint(
    payload: CrearLoteRequest,
    request: Request,
    _: None = _PERM_ENVIAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoteComunicacionResponse:
    """Crea un lote de mensajes salientes en estado Pendiente.

    Si len(destinatarios) > umbral_aprobacion → PendienteAprobacion (RN-17).
    Requiere permiso: `comunicacion:enviar`
    """
    settings = get_settings()

    lote = await crear_lote(
        asunto_tpl=payload.asunto_template,
        cuerpo_tpl=payload.cuerpo_template,
        destinatarios=[d.model_dump() for d in payload.destinatarios],
        materia_id=payload.materia_id,
        enviado_por=current_user.id,
        tenant_id=current_user.tenant_id,
        umbral_aprobacion=settings.comunicacion_umbral_aprobacion,
        db=db,
    )

    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=COMUNICACION_ENVIAR,
        materia_id=payload.materia_id,
        filas_afectadas=len(payload.destinatarios),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        detalle={"lote_id": str(lote.id), "requiere_aprobacion": lote.requiere_aprobacion},
    )

    await db.commit()
    await db.refresh(lote)
    return LoteComunicacionResponse.model_validate(lote)


@router.post(
    "/comunicaciones/lotes/{lote_id}/aprobar",
    response_model=LoteComunicacionResponse,
)
async def aprobar_lote_endpoint(
    lote_id: UUID,
    _: None = _PERM_APROBAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoteComunicacionResponse:
    """Aprueba un lote en estado PendienteAprobacion (RN-17).

    Requiere permiso: `comunicacion:aprobar`
    """
    lote = await aprobar_lote(
        lote_id=lote_id,
        aprobado_por=current_user.id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    await db.commit()
    await db.refresh(lote)
    return LoteComunicacionResponse.model_validate(lote)


@router.delete(
    "/comunicaciones/lotes/{lote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancelar_lote_endpoint(
    lote_id: UUID,
    _: None = _PERM_ENVIAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancela los mensajes Pendiente de un lote.

    No aplicable a lotes en Despachando o Completado.
    Requiere permiso: `comunicacion:enviar`
    """
    await cancelar_lote(
        lote_id=lote_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )
    await db.commit()


@router.get(
    "/comunicaciones/lotes",
    response_model=list[LoteComunicacionResponse],
)
async def listar_lotes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: None = _PERM_ENVIAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LoteComunicacionResponse]:
    """Lista los lotes de comunicación del tenant, ordenados por fecha descendente."""
    repo = ComunicacionRepository(db, tenant_id=current_user.tenant_id)
    lotes = await repo.list_lotes(limit=limit, offset=offset)
    return [LoteComunicacionResponse.model_validate(l) for l in lotes]
