"""Router de impersonación — inicio y fin de sesión de impersonación.

Endpoints:
  POST   /api/v1/auth/impersonate  → iniciar impersonación (emite token diferenciado)
  DELETE /api/v1/auth/impersonate  → finalizar impersonación

Ambos requieren autenticación. POST requiere además permiso 'impersonacion:usar'.
Toda acción queda registrada en el audit log (IMPERSONACION_INICIAR / FINALIZAR).

Reglas de seguridad:
  - La identidad del actor se extrae SIEMPRE del JWT (request.state.actor_id).
  - El usuario objetivo se busca en DB con scope del tenant del actor.
  - No se puede impersonar a un usuario de otro tenant.
  - Un token normal en DELETE retorna 400 (no hay sesión activa).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import IMPERSONACION_FINALIZAR, IMPERSONACION_INICIAR, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.security import create_access_token, verify_token
from app.repositories.user_repository import UserRepository
from app.schemas.impersonation import ImpersonateRequest, ImpersonateResponse

router = APIRouter(prefix="/api/v1/auth", tags=["impersonation"])


@router.post(
    "/impersonate",
    response_model=ImpersonateResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión de impersonación",
)
async def start_impersonation(
    body: ImpersonateRequest,
    request: Request,
    _: None = Depends(require_permission("impersonacion:usar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonateResponse:
    """Emite un token de acceso para operar en nombre de otro usuario.

    El token resultante tiene 'sub' = actor real y 'impersonated_id' = usuario objetivo.
    get_current_user resolverá la identidad efectiva como el usuario impersonado.

    Requiere permiso: `impersonacion:usar`
    """
    actor_id: UUID = request.state.actor_id
    tenant_id = current_user.tenant_id

    # Buscar el usuario objetivo en el mismo tenant del actor
    repo = UserRepository(db, tenant_id=tenant_id)
    target_user = await repo.get_by_id(body.user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en el tenant",
        )

    # Emitir token con actor real como 'sub' e impersonated_id en el payload
    token = create_access_token(
        data={
            "sub": str(actor_id),
            "tenant_id": str(tenant_id),
            "type": "access",
        },
        impersonated_id=target_user.id,
    )

    # Registrar inicio de impersonación
    await audit(
        db,
        actor_id=actor_id,
        tenant_id=tenant_id,
        accion=IMPERSONACION_INICIAR,
        impersonado_id=target_user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return ImpersonateResponse(access_token=token, token_type="bearer")


@router.delete(
    "/impersonate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Finalizar sesión de impersonación",
)
async def end_impersonation(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Registra el fin de una sesión de impersonación.

    Requiere que el token presente tenga 'impersonated_id'. Si el token
    es un token normal (sin impersonación), retorna 400.

    No emite nuevo token — el cliente debe usar su token original.
    """
    from jose import JWTError
    from fastapi.security import HTTPBearer

    # Extraer el token del header para verificar que tiene impersonated_id
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    raw_token = auth_header.removeprefix("Bearer ").strip()
    try:
        from app.core.security import verify_token
        payload = verify_token(raw_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    impersonated_id_raw = payload.get("impersonated_id")
    if not impersonated_id_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay sesión de impersonación activa",
        )

    try:
        impersonated_id = UUID(str(impersonated_id_raw))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token malformado")

    actor_id: UUID = request.state.actor_id
    tenant_id = current_user.tenant_id

    await audit(
        db,
        actor_id=actor_id,
        tenant_id=tenant_id,
        accion=IMPERSONACION_FINALIZAR,
        impersonado_id=impersonated_id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
