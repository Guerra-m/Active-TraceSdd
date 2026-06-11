"""Router de avisos institucionales y acknowledgments (C-15).

Endpoints:
  POST   /avisos              → crear aviso (avisos:publicar)
  GET    /avisos              → ver avisos visibles para el usuario actual
  PUT    /avisos/{id}         → editar aviso (avisos:publicar)
  DELETE /avisos/{id}         → soft delete (avisos:publicar)
  POST   /avisos/{id}/ack     → confirmar lectura (avisos:confirmar)
  GET    /avisos/{id}/stats   → contadores de acks (avisos:publicar)

RN-18/19/20: filtrado de scope y vigencia aplicado en AvisoService.
Regla #8: identidad SIEMPRE del JWT.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.aviso import AcknowledgmentAviso, Aviso
from app.repositories.aviso_repository import AcknowledgmentRepository, AvisoRepository
from app.schemas.avisos import (
    AckResponse,
    AvisoCreate,
    AvisoResponse,
    AvisoStatsResponse,
    AvisoUpdate,
)
from app.services.aviso_service import get_avisos_para_usuario

router = APIRouter(prefix="/api/v1/avisos", tags=["avisos"])

_PERM_PUBLICAR = Depends(require_permission("avisos:publicar"))
_PERM_CONFIRMAR = Depends(require_permission("avisos:confirmar"))


def _aviso_to_response(av: Aviso) -> AvisoResponse:
    return AvisoResponse(
        id=av.id,
        tenant_id=av.tenant_id,
        alcance=av.alcance,
        materia_id=av.materia_id,
        cohorte_id=av.cohorte_id,
        rol_destino=av.rol_destino,
        severidad=av.severidad,
        titulo=av.titulo,
        cuerpo=av.cuerpo,
        inicio_en=av.inicio_en,
        fin_en=av.fin_en,
        orden=av.orden,
        activo=av.activo,
        requiere_ack=av.requiere_ack,
    )


# ---------------------------------------------------------------------------
# POST /avisos — crear aviso
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AvisoResponse)
async def crear_aviso(
    payload: AvisoCreate,
    _: None = _PERM_PUBLICAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoResponse:
    av = Aviso(
        alcance=payload.alcance,
        materia_id=payload.materia_id,
        cohorte_id=payload.cohorte_id,
        rol_destino=payload.rol_destino,
        severidad=payload.severidad,
        titulo=payload.titulo,
        cuerpo=payload.cuerpo,
        inicio_en=payload.inicio_en,
        fin_en=payload.fin_en,
        orden=payload.orden,
        activo=payload.activo,
        requiere_ack=payload.requiere_ack,
    )
    repo = AvisoRepository(db, tenant_id=current_user.tenant_id)
    av = await repo.create(av)
    await db.commit()
    await db.refresh(av)
    return _aviso_to_response(av)


# ---------------------------------------------------------------------------
# GET /avisos — listar avisos visibles para el usuario actual
# ---------------------------------------------------------------------------


@router.get("", response_model=list[AvisoResponse])
async def listar_avisos(
    _: None = _PERM_CONFIRMAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AvisoResponse]:
    """Avisos visibles para el usuario: aplicando scope (RN-20) y vigencia (RN-18).

    Excluye avisos ack-eados cuando requiere_ack=True (RN-19).
    Ordenados por orden ASC.
    """
    avisos = await get_avisos_para_usuario(
        db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    return [_aviso_to_response(av) for av in avisos]


# ---------------------------------------------------------------------------
# PUT /avisos/{id} — editar aviso
# ---------------------------------------------------------------------------


@router.put("/{aviso_id}", response_model=AvisoResponse)
async def editar_aviso(
    aviso_id: UUID,
    payload: AvisoUpdate,
    _: None = _PERM_PUBLICAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoResponse:
    repo = AvisoRepository(db, tenant_id=current_user.tenant_id)
    av = await repo.get_by_id(aviso_id)
    if av is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

    if payload.titulo is not None:
        av.titulo = payload.titulo
    if payload.cuerpo is not None:
        av.cuerpo = payload.cuerpo
    if payload.severidad is not None:
        av.severidad = payload.severidad
    if payload.inicio_en is not None:
        av.inicio_en = payload.inicio_en
    if payload.fin_en is not None:
        av.fin_en = payload.fin_en
    if payload.orden is not None:
        av.orden = payload.orden
    if payload.activo is not None:
        av.activo = payload.activo

    av = await repo.update(av)
    await db.commit()
    await db.refresh(av)
    return _aviso_to_response(av)


# ---------------------------------------------------------------------------
# DELETE /avisos/{id} — soft delete
# ---------------------------------------------------------------------------


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_aviso(
    aviso_id: UUID,
    _: None = _PERM_PUBLICAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = AvisoRepository(db, tenant_id=current_user.tenant_id)
    ok = await repo.soft_delete(aviso_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")
    await db.commit()


# ---------------------------------------------------------------------------
# POST /avisos/{id}/ack — confirmar lectura (RN-19)
# ---------------------------------------------------------------------------


@router.post("/{aviso_id}/ack", status_code=status.HTTP_201_CREATED, response_model=AckResponse)
async def confirmar_lectura(
    aviso_id: UUID,
    _: None = _PERM_CONFIRMAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AckResponse:
    """Registra el acuse de recibo del usuario para el aviso."""
    aviso_repo = AvisoRepository(db, tenant_id=current_user.tenant_id)
    if await aviso_repo.get_by_id(aviso_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

    ack_repo = AcknowledgmentRepository(db, tenant_id=current_user.tenant_id)
    existente = await ack_repo.get_by_aviso_usuario(
        aviso_id=aviso_id, usuario_id=current_user.id
    )
    if existente is not None:
        return AckResponse(
            id=existente.id,
            aviso_id=existente.aviso_id,
            usuario_id=existente.usuario_id,
            confirmado_at=existente.confirmado_at,
        )

    ack = AcknowledgmentAviso(
        aviso_id=aviso_id,
        usuario_id=current_user.id,
        confirmado_at=datetime.now(timezone.utc),
    )
    ack = await ack_repo.create(ack)
    await db.commit()
    await db.refresh(ack)
    return AckResponse(
        id=ack.id,
        aviso_id=ack.aviso_id,
        usuario_id=ack.usuario_id,
        confirmado_at=ack.confirmado_at,
    )


# ---------------------------------------------------------------------------
# GET /avisos/{id}/stats — contadores de acks
# ---------------------------------------------------------------------------


@router.get("/{aviso_id}/stats", response_model=AvisoStatsResponse)
async def stats_aviso(
    aviso_id: UUID,
    _: None = _PERM_PUBLICAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoStatsResponse:
    aviso_repo = AvisoRepository(db, tenant_id=current_user.tenant_id)
    if await aviso_repo.get_by_id(aviso_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso no encontrado")

    ack_repo = AcknowledgmentRepository(db, tenant_id=current_user.tenant_id)
    total = await ack_repo.count_by_aviso(aviso_id)
    return AvisoStatsResponse(aviso_id=aviso_id, total_acks=total)
