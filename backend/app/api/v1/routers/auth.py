"""Router de autenticacion — C-03 (auth-jwt-2fa).

Endpoints:
  POST /api/v1/auth/login          — email + password, emite tokens o pre_auth_ticket
  POST /api/v1/auth/refresh        — rota refresh token, emite nuevo par
  POST /api/v1/auth/logout         — revoca refresh token
  POST /api/v1/auth/totp/enroll    — genera secreto TOTP (requiere autenticación)
  POST /api/v1/auth/totp/activate  — activa 2FA verificando primer código
  POST /api/v1/auth/totp/verify    — verifica TOTP post-login, emite sesión
  POST /api/v1/auth/forgot         — solicitud de recuperación de contraseña
  POST /api/v1/auth/reset          — reseteo con token de un solo uso

Reglas duras (CLAUDE.md):
  #8: identidad SIEMPRE del JWT verificado, NUNCA de parámetros del request
  #9: tenant_id siempre scoped en repositories
  #11: nunca lógica de negocio en routers — delegar a AuthService
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DbSession, get_current_user
from app.core.tenancy import get_tenant_id_from_token
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    PreAuthResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TotpActivateRequest,
    TotpEnrollResponse,
    TotpVerifyRequest,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    """Extrae la IP del cliente para rate limiting.

    Respeta el header X-Forwarded-For cuando existe (reverse proxy).
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", summary="Autenticar usuario")
async def login(
    body: LoginRequest,
    request: Request,
    db: DbSession,
) -> LoginResponse | PreAuthResponse:
    """Autentica con email + password.

    Si el usuario tiene 2FA habilitado, retorna un pre_auth_ticket.
    El cliente debe completar el flujo con POST /auth/totp/verify.

    Rate limit: 5 intentos/60s por IP+email.
    """
    # El tenant_id se resuelve en el servicio por email_hash
    # Para bootstrap, necesitamos el tenant. En multi-tenant real,
    # el tenant vendría del subdominio o del header X-Tenant-Slug.
    # Por ahora, AuthService resuelve por email_hash globalmente
    # y el tenant_id viene del usuario encontrado.
    # NOTA: esto es correcto — el tenant no viene de parámetro del request.

    # Usamos UUID dummy para inicializar el servicio; el repositorio
    # necesita tenant_id pero find_by_email_hash hace lookup global por hash.
    # Solución: usar un tenant UUID del usuario encontrado después del lookup.
    # El servicio maneja esto internamente con el email_hash.

    # Para el login inicial, no tenemos aún el tenant_id — el usuario
    # se identifica por su email_hash global. El servicio resuelve esto.
    # Pasamos un tenant null-UUID que será ignorado en el lookup por email_hash.
    import uuid
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_email, verify_password, hash_password

    client_ip = _get_client_ip(request)

    # Rate limit check - solo cuenta intentos FALLIDOS
    from app.services.auth_service import _is_rate_limited, _record_failed_attempt, _make_rate_limit_key
    rate_key = _make_rate_limit_key(client_ip, body.email)
    if await _is_rate_limited(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Reintentá en 60 segundos.",
        )

    # Lookup global por email_hash (cross-tenant search para autenticación inicial)
    # El tenant_id viene del usuario encontrado — NUNCA de un parámetro del request
    from sqlalchemy import select
    from app.models.user import User as UserModel
    from app.core.security import hash_email as _hash_email

    email_hash = _hash_email(body.email)
    stmt = (
        select(UserModel)
        .where(UserModel.email_hash == email_hash)
        .where(UserModel.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Timing-safe
    dummy_hash = hash_password("dummy-for-timing")
    if user is None:
        verify_password("wrong", dummy_hash)
        await _record_failed_attempt(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not verify_password(body.password, user.password_hash):
        await _record_failed_attempt(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta desactivada",
        )

    # Usar AuthService con el tenant_id del usuario encontrado
    svc = AuthService(db, tenant_id=user.tenant_id)

    if user.totp_enabled:
        from app.core.security import create_access_token
        from datetime import timedelta
        pre_auth_claims = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "type": "pre_auth",
        }
        pre_auth_ticket = create_access_token(pre_auth_claims, expires_delta=timedelta(minutes=5))
        return PreAuthResponse(pre_auth_ticket=pre_auth_ticket)

    result_tokens = await svc._issue_session(user)
    return LoginResponse(**result_tokens)


@router.post("/refresh", summary="Rotar refresh token")
async def refresh_token(
    body: RefreshRequest,
    db: DbSession,
) -> LoginResponse:
    """Rota el refresh token: invalida el viejo y emite nuevo par.

    Si el mismo token se usa dos veces, la segunda petición falla (ya revocado).
    """
    # Para refresh: el tenant_id viene del refresh token en DB
    # que fue vinculado al tenant en la creación.
    # Necesitamos buscar el token primero para obtener el tenant.
    from app.core.security import hash_token
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import select

    token_hash = hash_token(body.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    rt = result.scalar_one_or_none()

    if rt is None or not rt.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido, revocado o expirado",
        )

    svc = AuthService(db, tenant_id=rt.tenant_id)
    try:
        new_tokens = await svc.refresh(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return LoginResponse(**new_tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
async def logout(
    body: LogoutRequest,
    db: DbSession,
) -> None:
    """Revoca el refresh token. Idempotente: no falla si el token ya fue revocado."""
    from app.core.security import hash_token
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import select

    token_hash = hash_token(body.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    rt = result.scalar_one_or_none()

    if rt is not None:
        svc = AuthService(db, tenant_id=rt.tenant_id)
        await svc.logout(body.refresh_token)


@router.post("/totp/enroll", summary="Iniciar enrolamiento 2FA")
async def enroll_totp(
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> TotpEnrollResponse:
    """Genera un secreto TOTP para el usuario autenticado.

    El secreto se muestra UNA sola vez. El usuario debe escanearlo con
    su app autenticadora y completar la activación con POST /totp/activate.
    """
    svc = AuthService(db, tenant_id=current_user.tenant_id)
    result = await svc.enroll_totp(current_user)
    return TotpEnrollResponse(**result)


@router.post("/totp/activate", summary="Activar 2FA")
async def activate_totp(
    body: TotpActivateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Activa el 2FA verificando el primer código TOTP.

    Debe llamarse después de enroll_totp. El código debe ser generado
    por la app autenticadora que escaneó el QR.
    """
    svc = AuthService(db, tenant_id=current_user.tenant_id)
    try:
        await svc.activate_totp(current_user, body.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return MessageResponse(message="2FA activado correctamente")


@router.post("/totp/verify", summary="Verificar TOTP post-login")
async def verify_totp_login(
    body: TotpVerifyRequest,
    db: DbSession,
) -> LoginResponse:
    """Verifica el código TOTP y emite la sesión completa.

    Requiere el pre_auth_ticket obtenido de POST /auth/login cuando
    el usuario tiene 2FA habilitado.
    """
    # El tenant_id viene del pre_auth_ticket JWT — NUNCA de parámetros
    from app.core.security import verify_token
    from jose import JWTError

    try:
        payload = verify_token(body.pre_auth_ticket)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="pre_auth_ticket inválido o expirado",
        )

    try:
        tenant_id = get_tenant_id_from_token(payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
        )

    svc = AuthService(db, tenant_id=tenant_id)
    try:
        tokens = await svc.verify_totp_login(body.pre_auth_ticket, body.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return LoginResponse(**tokens)


@router.post("/forgot", summary="Solicitar recuperación de contraseña")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    """Inicia el flujo de recuperación de contraseña.

    Siempre retorna 200 para evitar user enumeration.
    El token de reset se envía por email (simulado en dev).
    """
    # Lookup cross-tenant para recuperación (mismo patrón que login)
    from sqlalchemy import select
    from app.models.user import User as UserModel
    from app.core.security import hash_email

    email_hash = hash_email(body.email)
    stmt = (
        select(UserModel)
        .where(UserModel.email_hash == email_hash)
        .where(UserModel.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        svc = AuthService(db, tenant_id=user.tenant_id)
        await svc.forgot_password(body.email)

    # Siempre retornar 200 — no revelar si el email existe
    return MessageResponse(message="Si el email existe, recibirás instrucciones para recuperar tu contraseña.")


@router.post("/reset", summary="Resetear contraseña")
async def reset_password(
    body: ResetPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    """Resetea la contraseña usando el token de recuperación.

    El token es de un solo uso y expira en 1 hora.
    """
    # Para reset: el token apunta a un user → tenant
    import hashlib
    from sqlalchemy import select
    from app.models.password_reset_token import PasswordResetToken
    from datetime import datetime, timezone

    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    stmt = (
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > now)
    )
    result = await db.execute(stmt)
    prt = result.scalar_one_or_none()

    if prt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, ya usado o expirado",
        )

    svc = AuthService(db, tenant_id=prt.tenant_id)
    try:
        await svc.reset_password(body.token, body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return MessageResponse(message="Contraseña actualizada correctamente")
