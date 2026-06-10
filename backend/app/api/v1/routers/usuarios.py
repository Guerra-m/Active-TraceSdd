"""Router de usuarios — gestión de perfil docente y PII.

Endpoints:
  GET    /admin/usuarios             → lista usuarios del tenant (sin PII)
  POST   /admin/usuarios             → crear usuario con perfil (201)
  GET    /admin/usuarios/{id}        → obtener usuario (sin PII)
  PUT    /admin/usuarios/{id}        → actualizar perfil
  DELETE /admin/usuarios/{id}        → soft delete (204)
  GET    /admin/usuarios/{id}/pii    → perfil con PII desencriptada (requiere mismo permiso + audit log)

Todos los endpoints requieren `usuarios:gestionar`.
El endpoint /pii además registra USUARIO_VER_PII en audit_log.

Flujo (regla #11): Router → Repository → Models.
Identidad desde JWT (regla #8); PII descifrada solo en endpoint dedicado.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import USUARIO_CREAR, USUARIO_DESACTIVAR, USUARIO_VER_PII, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.encryption import decrypt
from app.repositories.user_repository import UserRepository
from app.schemas.usuarios import (
    UsuarioCreate,
    UsuarioPIIResponse,
    UsuarioResponse,
    UsuarioUpdate,
)

router = APIRouter(prefix="/api/v1/admin", tags=["usuarios"])

_PERM = Depends(require_permission("usuarios:gestionar"))


@router.get("/usuarios", response_model=list[UsuarioResponse])
async def list_usuarios(
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UsuarioResponse]:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list()
    return [UsuarioResponse.model_validate(u) for u in items]


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    try:
        user = await repo.create_usuario(
            email=payload.email,
            password_plaintext=payload.password,
            nombre=payload.nombre,
            apellidos=payload.apellidos,
            dni=payload.dni,
            cuil=payload.cuil,
            cbu=payload.cbu,
            alias_cbu=payload.alias_cbu,
            banco=payload.banco,
            regional=payload.regional,
            legajo=payload.legajo,
            legajo_profesional=payload.legajo_profesional,
            facturador=payload.facturador,
            estado=payload.estado,
        )
        await audit(
            db,
            actor_id=request.state.actor_id,
            tenant_id=current_user.tenant_id,
            accion=USUARIO_CREAR,
            detalle={"usuario_id": str(user.id)},
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado en este tenant",
        )
    return UsuarioResponse.model_validate(user)


@router.get("/usuarios/{id}", response_model=UsuarioResponse)
async def get_usuario(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    user = await repo.get_by_id(id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UsuarioResponse.model_validate(user)


@router.put("/usuarios/{id}", response_model=UsuarioResponse)
async def update_usuario(
    id: UUID,
    payload: UsuarioUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    campos = payload.model_dump(exclude_unset=True)
    user = await repo.update_perfil(id, campos)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await db.commit()
    return UsuarioResponse.model_validate(user)


@router.delete("/usuarios/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=USUARIO_DESACTIVAR,
        detalle={"usuario_id": str(id)},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


@router.get("/usuarios/{id}/pii", response_model=UsuarioPIIResponse)
async def get_usuario_pii(
    id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioPIIResponse:
    """Retorna perfil con PII desencriptada. Requiere permiso usuarios:gestionar.

    Registra USUARIO_VER_PII en audit_log con actor, IP y user-agent.
    """
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    user = await repo.get_by_id(id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=USUARIO_VER_PII,
        detalle={"usuario_id": str(id)},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return UsuarioPIIResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        nombre=user.nombre,
        apellidos=user.apellidos,
        dni=decrypt(user.dni_encrypted) if user.dni_encrypted else None,
        cuil=decrypt(user.cuil_encrypted) if user.cuil_encrypted else None,
        cbu=decrypt(user.cbu_encrypted) if user.cbu_encrypted else None,
        alias_cbu=decrypt(user.alias_cbu_encrypted) if user.alias_cbu_encrypted else None,
        banco=user.banco,
        regional=user.regional,
        legajo=user.legajo,
        legajo_profesional=user.legajo_profesional,
        facturador=user.facturador,
        estado=user.estado,
    )
