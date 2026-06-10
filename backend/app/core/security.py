"""Modulo de seguridad — autenticacion JWT, Argon2id, TOTP.

Implementa C-03 (auth-jwt-2fa):
  - Hashing y verificacion de passwords con Argon2id (argon2-cffi)
  - Hash determinístico de email (SHA-256, normalizado) para búsquedas
  - Generacion y verificacion de tokens JWT (access + refresh rotation)
  - Generacion y verificacion TOTP (pyotp)
  - Generacion de refresh tokens opacos con hash SHA-256

Reglas duras aplicables (ver CLAUDE.md):
  - La identidad SIEMPRE desde el JWT verificado, NUNCA desde params de request (#8)
  - Passwords con Argon2id; NUNCA texto plano (#12)
  - UUID interno como identificador (#14)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Argon2id — password hashing
# ---------------------------------------------------------------------------

# Instancia compartida con parámetros seguros (argon2-cffi defaults son buenos)
_ph = PasswordHasher()


def hash_password(plaintext: str) -> str:
    """Hashea un password con Argon2id.

    Args:
        plaintext: Password en texto plano.

    Returns:
        Hash Argon2id serializado como string (formato $argon2id$...).
    """
    return _ph.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verifica un password contra su hash Argon2id.

    Args:
        plaintext: Password a verificar.
        hashed: Hash Argon2id almacenado.

    Returns:
        True si el password es correcto, False en caso contrario.
        Nunca lanza excepción — retorna False ante cualquier error.
    """
    try:
        return _ph.verify(hashed, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ---------------------------------------------------------------------------
# Email hash — lookup determinístico sin exponer el email
# ---------------------------------------------------------------------------


def hash_email(email: str) -> str:
    """Retorna el hash SHA-256 del email normalizado.

    Normalización: lowercase + strip. Esto garantiza que el mismo email
    produce siempre el mismo hash, independientemente de mayúsculas o
    espacios accidentales.

    Args:
        email: Email a hashear.

    Returns:
        String hexadecimal de 64 caracteres (SHA-256).
    """
    normalized = email.lower().strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# JWT — access token y pre_auth_ticket
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un JWT access token firmado con HS256.

    Args:
        data: Claims a incluir en el payload. Debe contener al menos
              'sub' (user_id como string), 'tenant_id', 'roles'.
        expires_delta: Tiempo de vida. Si es None, usa ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        JWT firmado como string.
    """
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verifica la firma y expiración de un JWT y retorna el payload.

    Args:
        token: JWT a verificar.

    Returns:
        Payload decodificado como dict.

    Raises:
        JWTError: Si el token es inválido, expirado o la firma no coincide.
    """
    settings = get_settings()
    # JWTError se propaga al llamador (router/dependency lo convierte a 401)
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    return payload


# ---------------------------------------------------------------------------
# Refresh token — opaco, solo el hash en DB
# ---------------------------------------------------------------------------


def create_refresh_token() -> tuple[str, str]:
    """Genera un refresh token opaco y su hash SHA-256.

    Returns:
        Tupla (token_raw, token_hash) donde:
          - token_raw: valor crudo URL-safe de 64 bytes — emitir al cliente UNA vez
          - token_hash: SHA-256 del token_raw — lo que se guarda en DB

    Regla (design D2): nunca persistir token_raw. Solo token_hash va a la BD.
    """
    token_raw = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()
    return token_raw, token_hash


def hash_token(token_raw: str) -> str:
    """Hashea un token opaco para comparar contra la DB.

    Args:
        token_raw: Token crudo recibido del cliente.

    Returns:
        SHA-256 hexadecimal del token.
    """
    return hashlib.sha256(token_raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# TOTP — 2FA con pyotp
# ---------------------------------------------------------------------------


def generate_totp_secret() -> str:
    """Genera un secreto TOTP aleatorio compatible con RFC 6238.

    Returns:
        Secreto Base32 de 32 caracteres (160 bits de entropía).
    """
    return pyotp.random_base32()


def verify_totp(secret_plaintext: str, code: str) -> bool:
    """Verifica un código TOTP contra el secreto en texto plano.

    Args:
        secret_plaintext: Secreto TOTP (ya descifrado, nunca el valor cifrado).
        code: Código de 6 dígitos ingresado por el usuario.

    Returns:
        True si el código es válido (ventana de ±1 intervalo de 30s).
        False si es inválido o cualquier error ocurre.
    """
    try:
        totp = pyotp.TOTP(secret_plaintext)
        # valid_window=1 acepta el código del intervalo anterior/siguiente
        # para tolerar desincronización de reloj
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def get_totp_uri(secret_plaintext: str, email: str, issuer: str = "active-trace") -> str:
    """Genera el URI otpauth:// para mostrar el QR de enrolamiento TOTP.

    Args:
        secret_plaintext: Secreto TOTP en texto plano.
        email: Email del usuario (label del QR).
        issuer: Nombre del emisor (mostrado en la app autenticadora).

    Returns:
        URI otpauth:// compatible con Google Authenticator, Authy, etc.
    """
    totp = pyotp.TOTP(secret_plaintext)
    return totp.provisioning_uri(name=email, issuer_name=issuer)
