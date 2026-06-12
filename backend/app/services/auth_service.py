"""Servicio de autenticacion — logica de negocio de auth.

Implementa C-03 (auth-jwt-2fa). Capa de servicio: NUNCA accede directo a DB,
SIEMPRE via repositories. NUNCA lanza HTTPException — retorna resultados
o lanza ValueError/PermissionError que el router convierte a HTTP.

Operaciones:
  - login             : valida credenciales, rate limit, emite tokens
  - refresh           : rota refresh token, emite nuevo par
  - logout            : revoca refresh token
  - enroll_totp       : genera secreto TOTP para el usuario
  - activate_totp     : activa 2FA verificando el primer código
  - verify_totp_login : verifica TOTP tras pre_auth_ticket, emite sesión
  - forgot_password   : genera token de reset y simula envío de email
  - reset_password    : consume token de reset, actualiza password

Rate limiting (design D4):
  In-memory, 5 intentos/60s por clave IP+email_hash.
  Thread-safe a nivel asyncio (no multiprocess).
"""

import asyncio
import time
from collections import defaultdict
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt, encrypt
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_totp_secret,
    get_totp_uri,
    hash_email,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
    verify_totp,
)
from app.models.user import User
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# Rate limiter in-memory (design D4)
# ---------------------------------------------------------------------------

_RATE_LIMIT_MAX_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 60

# {key: [timestamps de intentos dentro de la ventana]}
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_rate_limit_lock = asyncio.Lock()


async def _is_rate_limited(key: str) -> bool:
    """Devuelve True si la clave superó el límite de intentos fallidos."""
    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    async with _rate_limit_lock:
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > cutoff]
        return len(_rate_limit_store[key]) >= _RATE_LIMIT_MAX_ATTEMPTS


async def _record_failed_attempt(key: str) -> None:
    """Registra un intento fallido de login para rate limiting."""
    async with _rate_limit_lock:
        _rate_limit_store[key].append(time.monotonic())


def _make_rate_limit_key(ip: str, email: str) -> str:
    """Genera la clave de rate limit: IP + email_hash."""
    return f"{ip}:{hash_email(email)}"


# ---------------------------------------------------------------------------
# Helpers para construcción de tokens
# ---------------------------------------------------------------------------

def _build_access_token_claims(user: User) -> dict:
    """Construye el payload del access token.

    Claims mínimos según spec: user_id, tenant_id, roles, exp.
    roles se deja como lista vacía — C-04 (RBAC) los populará.
    """
    return {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "roles": [],  # C-04 (rbac) populará este campo
        "type": "access",
    }


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------

class AuthService:
    """Servicio de autenticacion. Recibe la sesión por constructor.

    Uso en routers:
        svc = AuthService(db, tenant_id=tenant_id)
        result = await svc.login(email, password, ip)
    """

    def __init__(self, db: AsyncSession, *, tenant_id: UUID) -> None:
        self._db = db
        self._tenant_id = tenant_id
        self._user_repo = UserRepository(db, tenant_id=tenant_id)
        self._rt_repo = RefreshTokenRepository(db, tenant_id=tenant_id)
        self._prt_repo = PasswordResetTokenRepository(db, tenant_id=tenant_id)

    async def login(
        self,
        email: str,
        password: str,
        client_ip: str,
        refresh_token_expire_days: int = 30,
    ) -> dict:
        """Autentica un usuario con email + password.

        Si el usuario tiene 2FA habilitado, retorna un pre_auth_ticket en lugar
        de la sesión completa. El cliente debe completar con /auth/totp/verify.

        Args:
            email: Email del usuario.
            password: Password en texto plano.
            client_ip: IP del cliente para rate limiting.
            refresh_token_expire_days: Días de vida del refresh token.

        Returns:
            dict con 'access_token' + 'refresh_token' (sin 2FA), o
            dict con 'pre_auth_ticket' (con 2FA habilitado).

        Raises:
            PermissionError: Si se superó el rate limit (429).
            ValueError: Si las credenciales son incorrectas.
        """
        from datetime import datetime, timezone

        # Rate limit — solo cuenta intentos FALLIDOS (sliding window)
        rate_key = _make_rate_limit_key(client_ip, email)
        if await _is_rate_limited(rate_key):
            raise PermissionError("Demasiados intentos. Reintentá en 60 segundos.")

        # Buscar usuario por email (lookup via hash)
        user = await self._user_repo.find_by_email_hash(email)

        # Timing-safe: verificar password incluso si el usuario no existe
        # para evitar timing attacks que detecten si el email existe.
        dummy_hash = hash_password("dummy-for-timing")
        if user is None:
            verify_password("wrong", dummy_hash)
            await _record_failed_attempt(rate_key)
            raise ValueError("Credenciales incorrectas")

        if not verify_password(password, user.password_hash):
            await _record_failed_attempt(rate_key)
            raise ValueError("Credenciales incorrectas")

        if not user.is_active:
            raise ValueError("Cuenta desactivada")

        # Si 2FA está habilitado → emitir pre_auth_ticket (no sesión completa)
        if user.totp_enabled:
            pre_auth_claims = {
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
                "type": "pre_auth",
            }
            pre_auth_ticket = create_access_token(
                pre_auth_claims,
                expires_delta=timedelta(minutes=5),
            )
            return {"pre_auth_ticket": pre_auth_ticket}

        # Sin 2FA → emitir sesión completa
        return await self._issue_session(user, refresh_token_expire_days)

    async def _issue_session(self, user: User, refresh_token_expire_days: int = 30) -> dict:
        """Emite un par access + refresh token para el usuario.

        Returns:
            dict con 'access_token', 'refresh_token', 'token_type', 'user', 'permissions'.
        """
        from datetime import date, datetime, timezone

        from sqlalchemy import and_, select

        from app.models.permiso import Permiso
        from app.models.rol import Rol
        from app.models.rol_permiso import RolPermiso
        from app.models.usuario_rol import UsuarioRol

        # Access token
        access_token = create_access_token(_build_access_token_claims(user))

        # Refresh token — solo el hash en DB
        token_raw, token_hash = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=refresh_token_expire_days)
        await self._rt_repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Roles activos del usuario
        today = date.today()
        roles_stmt = (
            select(Rol.code)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(
                UsuarioRol.user_id == user.id,
                UsuarioRol.deleted_at.is_(None),
                UsuarioRol.valid_from <= today,
                (UsuarioRol.valid_until.is_(None)) | (UsuarioRol.valid_until >= today),
                Rol.deleted_at.is_(None),
                Rol.is_active.is_(True),
            )
        )
        roles_result = await self._db.execute(roles_stmt)
        role_codes = [r for (r,) in roles_result.all()]

        # Permisos activos del usuario (vía sus roles)
        perms_stmt = (
            select(Permiso.code)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.rol_id)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(
                UsuarioRol.user_id == user.id,
                UsuarioRol.deleted_at.is_(None),
                UsuarioRol.valid_from <= today,
                (UsuarioRol.valid_until.is_(None)) | (UsuarioRol.valid_until >= today),
                Rol.deleted_at.is_(None),
                Rol.is_active.is_(True),
                Permiso.is_active.is_(True),
            )
            .distinct()
        )
        perms_result = await self._db.execute(perms_stmt)
        permissions = [p for (p,) in perms_result.all()]

        email = decrypt(user.email_encrypted)

        return {
            "access_token": access_token,
            "refresh_token": token_raw,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": email,
                "nombre": user.nombre or "",
                "rol": role_codes[0] if role_codes else "",
                "tenant_id": str(user.tenant_id),
            },
            "permissions": permissions,
        }

    async def refresh(self, refresh_token_raw: str, refresh_token_expire_days: int = 30) -> dict:
        """Rota un refresh token: revoca el viejo, emite nuevo par.

        Args:
            refresh_token_raw: Token crudo recibido del cliente.
            refresh_token_expire_days: Días de vida del nuevo refresh token.

        Returns:
            dict con nuevo 'access_token' y 'refresh_token'.

        Raises:
            ValueError: Si el token no existe, está revocado o expiró.
        """
        token_hash = hash_token(refresh_token_raw)
        rt = await self._rt_repo.find_by_hash(token_hash)

        if rt is None or not rt.is_valid():
            raise ValueError("Refresh token inválido, revocado o expirado")

        # Revocar el token viejo ANTES de emitir el nuevo (rotación atómica)
        await self._rt_repo.revoke(token_hash)

        # Obtener el usuario para construir los claims
        user = await self._user_repo.get_by_id(rt.user_id)
        if user is None or not user.is_active:
            raise ValueError("Usuario no encontrado o desactivado")

        return await self._issue_session(user, refresh_token_expire_days)

    async def logout(self, refresh_token_raw: str) -> None:
        """Revoca el refresh token (cierre de sesión).

        Args:
            refresh_token_raw: Token crudo a revocar.

        Note:
            No lanza error si el token no existe (idempotente).
        """
        token_hash = hash_token(refresh_token_raw)
        await self._rt_repo.revoke(token_hash)

    async def enroll_totp(self, user: User) -> dict:
        """Genera un secreto TOTP para el usuario y lo persiste cifrado.

        No activa el 2FA todavía — el usuario debe completar la verificación
        con activate_totp() para confirmar que guardó el secreto.

        Args:
            user: Usuario autenticado.

        Returns:
            dict con 'secret' (texto plano, mostrar UNA vez) y 'qr_uri'.
        """
        secret_plaintext = generate_totp_secret()
        user.totp_secret_encrypted = encrypt(secret_plaintext)
        await self._user_repo.update(user)

        # Descifrar email para el QR URI (mostrar en la app autenticadora)
        try:
            email_plaintext = decrypt(user.email_encrypted)
        except Exception:
            email_plaintext = "usuario"

        qr_uri = get_totp_uri(secret_plaintext, email_plaintext)

        return {"secret": secret_plaintext, "qr_uri": qr_uri}

    async def activate_totp(self, user: User, code: str) -> None:
        """Activa el 2FA verificando el primer código TOTP.

        Args:
            user: Usuario autenticado.
            code: Código de 6 dígitos del autenticador.

        Raises:
            ValueError: Si el código es inválido o el secreto no está configurado.
        """
        if not user.totp_secret_encrypted:
            raise ValueError("2FA no configurado — llamar primero a enroll_totp")

        secret_plaintext = decrypt(user.totp_secret_encrypted)
        if not verify_totp(secret_plaintext, code):
            raise ValueError("Código TOTP inválido")

        user.totp_enabled = True
        await self._user_repo.update(user)

    async def verify_totp_login(
        self,
        pre_auth_ticket: str,
        code: str,
        refresh_token_expire_days: int = 30,
    ) -> dict:
        """Verifica TOTP post-login y emite sesión completa.

        Args:
            pre_auth_ticket: JWT de tipo 'pre_auth' obtenido del login.
            code: Código TOTP del autenticador.
            refresh_token_expire_days: Días de vida del refresh token.

        Returns:
            dict con 'access_token' y 'refresh_token'.

        Raises:
            ValueError: Si el ticket es inválido, el código incorrecto, etc.
        """
        from jose import JWTError

        try:
            payload = verify_token(pre_auth_ticket)
        except JWTError as exc:
            raise ValueError("pre_auth_ticket inválido o expirado") from exc

        if payload.get("type") != "pre_auth":
            raise ValueError("Token inválido — se esperaba pre_auth_ticket")

        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise ValueError("pre_auth_ticket malformado")

        try:
            user_id = UUID(str(user_id_raw))
        except ValueError as exc:
            raise ValueError("pre_auth_ticket malformado") from exc

        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise ValueError("Usuario no encontrado")

        if not user.totp_secret_encrypted:
            raise ValueError("2FA no configurado")

        secret_plaintext = decrypt(user.totp_secret_encrypted)
        if not verify_totp(secret_plaintext, code):
            raise ValueError("Código TOTP inválido")

        return await self._issue_session(user, refresh_token_expire_days)

    async def forgot_password(self, email: str) -> str | None:
        """Inicia la recuperación de contraseña.

        Genera un token de un solo uso (1h) y simula el envío por email.
        No revela si el email existe (evita user enumeration).

        Args:
            email: Email del usuario.

        Returns:
            Token crudo (solo para tests/simulación — en prod se enviaría por email).
            None si el usuario no existe (respuesta idéntica al exterior).
        """
        import secrets as _secrets
        import hashlib
        from datetime import datetime, timezone

        user = await self._user_repo.find_by_email_hash(email)
        if user is None:
            # No revelar si el email existe — retornar None silenciosamente
            return None

        # Generar token de un solo uso
        token_raw = _secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await self._prt_repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # TODO (C-08 comunicacion): enviar token por email en producción
        # Por ahora se retorna el token crudo para tests de integración
        return token_raw

    async def reset_password(self, token_raw: str, new_password: str) -> None:
        """Resetea el password usando un token de recuperación.

        Args:
            token_raw: Token crudo enviado por email.
            new_password: Nuevo password en texto plano (mín 8 chars).

        Raises:
            ValueError: Si el token es inválido, ya fue usado o expiró.
        """
        import hashlib

        token_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()
        prt = await self._prt_repo.find_valid_by_hash(token_hash)

        if prt is None:
            raise ValueError("Token de recuperación inválido, ya usado o expirado")

        # Marcar como usado ANTES de actualizar el password (un solo uso)
        await self._prt_repo.mark_used(token_hash)

        # Actualizar password
        user = await self._user_repo.get_by_id(prt.user_id)
        if user is None:
            raise ValueError("Usuario no encontrado")

        user.password_hash = hash_password(new_password)
        await self._user_repo.update(user)
