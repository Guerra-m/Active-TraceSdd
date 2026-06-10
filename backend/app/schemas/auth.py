"""Schemas Pydantic para los endpoints de autenticacion.

Todos los schemas usan `extra='forbid'` (regla dura #5):
  - Rechaza campos no declarados para evitar parameter injection.
  - En request schemas: evita que el cliente pase campos no esperados.
  - En response schemas: garantiza shape predictible.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Configuración compartida
# ---------------------------------------------------------------------------

class _StrictModel(BaseModel):
    """Base con extra='forbid' para todos los schemas de auth."""
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(_StrictModel):
    """Credenciales de login. El código TOTP es opcional.

    Si el usuario tiene 2FA habilitado, el servidor emitirá un pre_auth_ticket
    en lugar de la sesión completa. El cliente debe completar el flujo TOTP.
    """
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(_StrictModel):
    """Respuesta de login exitoso (sin 2FA o con 2FA ya verificado)."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PreAuthResponse(_StrictModel):
    """Respuesta de login cuando 2FA está habilitado.

    El cliente debe enviar este ticket junto al código TOTP a /auth/totp/verify.
    El ticket expira en 5 minutos.
    """
    pre_auth_ticket: str
    message: str = "Se requiere verificación TOTP"


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class RefreshRequest(_StrictModel):
    """Token de refresh para rotar la sesión."""
    refresh_token: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutRequest(_StrictModel):
    """Cierra la sesión revocando el refresh token activo."""
    refresh_token: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# TOTP — 2FA
# ---------------------------------------------------------------------------

class TotpEnrollResponse(_StrictModel):
    """Datos de enrolamiento TOTP para mostrar al usuario.

    El secreto se muestra UNA vez y el QR se genera para la app autenticadora.
    Después del primer verify exitoso, el 2FA queda habilitado.
    """
    secret: str
    qr_uri: str


class TotpVerifyRequest(_StrictModel):
    """Verificación TOTP post-login (completa el flujo de 2FA).

    El pre_auth_ticket se obtiene de la respuesta de /auth/login cuando
    el usuario tiene 2FA habilitado.
    """
    pre_auth_ticket: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TotpActivateRequest(_StrictModel):
    """Activa el 2FA verificando el primer código tras el enrolamiento."""
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------

class ForgotPasswordRequest(_StrictModel):
    """Solicitud de recuperación — inicia el flujo enviando token por email."""
    email: EmailStr


class ResetPasswordRequest(_StrictModel):
    """Reseteo de contraseña con token de un solo uso."""
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


# ---------------------------------------------------------------------------
# Respuestas genéricas
# ---------------------------------------------------------------------------

class MessageResponse(_StrictModel):
    """Respuesta de confirmación genérica."""
    message: str
