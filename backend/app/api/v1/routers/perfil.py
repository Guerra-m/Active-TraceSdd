"""Router de perfil propio y mensajería interna (C-20).

Endpoints:
  GET  /api/v1/perfil          → ver perfil propio (perfil:editar)
  PUT  /api/v1/perfil          → editar perfil (campos editables; CUIL solo lectura)
  GET  /api/v1/inbox           → listar hilos del usuario (inbox:usar)
  POST /api/v1/inbox           → crear hilo nuevo con primer mensaje (inbox:usar)
  GET  /api/v1/inbox/{id}      → mensajes de un hilo (inbox:usar)
  POST /api/v1/inbox/{id}      → responder en un hilo (inbox:usar)

Regla #8: identidad SIEMPRE del JWT — nunca de parámetros de request.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.encryption import decrypt
from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.repositories.inbox_repository import HiloMensajeRepository, MensajeInternoRepository
from app.repositories.user_repository import UserRepository
from app.schemas.perfil import (
    HiloMensajeCreate,
    HiloMensajeResponse,
    MensajeInternoCreate,
    MensajeInternoResponse,
    PerfilResponse,
    PerfilUpdate,
)

router = APIRouter(tags=["perfil-inbox"])

_PERM_PERFIL = Depends(require_permission("perfil:editar"))
_PERM_INBOX = Depends(require_permission("inbox:usar"))


def _safe_decrypt(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return decrypt(value)
    except Exception:
        return None


def _user_to_perfil(u) -> PerfilResponse:
    return PerfilResponse(
        id=u.id,
        tenant_id=u.tenant_id,
        nombre=u.nombre,
        apellidos=u.apellidos,
        banco=u.banco,
        regional=u.regional,
        legajo=u.legajo,
        legajo_profesional=u.legajo_profesional,
        facturador=u.facturador,
        cuil=_safe_decrypt(u.cuil_encrypted),
        cbu=_safe_decrypt(u.cbu_encrypted),
        alias_cbu=_safe_decrypt(u.alias_cbu_encrypted),
        is_active=u.is_active,
    )


def _hilo_to_response(h: HiloMensaje) -> HiloMensajeResponse:
    return HiloMensajeResponse(
        id=h.id,
        tenant_id=h.tenant_id,
        asunto=h.asunto,
        remitente_id=h.remitente_id,
        destinatario_id=h.destinatario_id,
    )


def _mensaje_to_response(m: MensajeInterno) -> MensajeInternoResponse:
    return MensajeInternoResponse(
        id=m.id,
        hilo_id=m.hilo_id,
        autor_id=m.autor_id,
        cuerpo=m.cuerpo,
    )


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------


@router.get("/api/v1/perfil", response_model=PerfilResponse)
async def get_perfil(
    _: None = _PERM_PERFIL,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerfilResponse:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    user = await repo.get_by_id(current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _user_to_perfil(user)


@router.put("/api/v1/perfil", response_model=PerfilResponse)
async def update_perfil(
    payload: PerfilUpdate,
    _: None = _PERM_PERFIL,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerfilResponse:
    campos = payload.model_dump(exclude_none=True)
    if not campos:
        # Nada para actualizar — devolver perfil actual
        repo = UserRepository(db, tenant_id=current_user.tenant_id)
        user = await repo.get_by_id(current_user.id)
        return _user_to_perfil(user)

    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    user = await repo.update_perfil(current_user.id, campos)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await db.commit()
    await db.refresh(user)
    return _user_to_perfil(user)


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------


@router.get("/api/v1/inbox", response_model=list[HiloMensajeResponse])
async def listar_hilos(
    _: None = _PERM_INBOX,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HiloMensajeResponse]:
    repo = HiloMensajeRepository(db, tenant_id=current_user.tenant_id)
    hilos = await repo.list_para_usuario(current_user.id)
    return [_hilo_to_response(h) for h in hilos]


@router.post("/api/v1/inbox", status_code=status.HTTP_201_CREATED, response_model=HiloMensajeResponse)
async def crear_hilo(
    payload: HiloMensajeCreate,
    _: None = _PERM_INBOX,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HiloMensajeResponse:
    hilo_repo = HiloMensajeRepository(db, tenant_id=current_user.tenant_id)
    msg_repo = MensajeInternoRepository(db, tenant_id=current_user.tenant_id)

    hilo = HiloMensaje(
        asunto=payload.asunto,
        remitente_id=current_user.id,
        destinatario_id=payload.destinatario_id,
    )
    hilo = await hilo_repo.create(hilo)
    await db.flush()

    msg = MensajeInterno(
        hilo_id=hilo.id,
        autor_id=current_user.id,
        cuerpo=payload.primer_mensaje,
    )
    await msg_repo.create(msg)
    await db.commit()
    await db.refresh(hilo)
    return _hilo_to_response(hilo)


@router.get("/api/v1/inbox/{hilo_id}", response_model=list[MensajeInternoResponse])
async def get_mensajes(
    hilo_id: UUID,
    _: None = _PERM_INBOX,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MensajeInternoResponse]:
    hilo_repo = HiloMensajeRepository(db, tenant_id=current_user.tenant_id)
    hilo = await hilo_repo.get_by_id(hilo_id)
    if hilo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hilo no encontrado")
    # Solo participantes del hilo pueden ver sus mensajes
    if hilo.remitente_id != current_user.id and hilo.destinatario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este hilo")

    msg_repo = MensajeInternoRepository(db, tenant_id=current_user.tenant_id)
    mensajes = await msg_repo.list_by_hilo(hilo_id)
    return [_mensaje_to_response(m) for m in mensajes]


@router.post("/api/v1/inbox/{hilo_id}", status_code=status.HTTP_201_CREATED, response_model=MensajeInternoResponse)
async def responder_hilo(
    hilo_id: UUID,
    payload: MensajeInternoCreate,
    _: None = _PERM_INBOX,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MensajeInternoResponse:
    hilo_repo = HiloMensajeRepository(db, tenant_id=current_user.tenant_id)
    hilo = await hilo_repo.get_by_id(hilo_id)
    if hilo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hilo no encontrado")
    if hilo.remitente_id != current_user.id and hilo.destinatario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este hilo")

    msg_repo = MensajeInternoRepository(db, tenant_id=current_user.tenant_id)
    msg = MensajeInterno(
        hilo_id=hilo_id,
        autor_id=current_user.id,
        cuerpo=payload.cuerpo,
    )
    msg = await msg_repo.create(msg)
    await db.commit()
    await db.refresh(msg)
    return _mensaje_to_response(msg)
