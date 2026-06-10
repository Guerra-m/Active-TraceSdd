"""Dependencies de FastAPI para inyeccion de dependencias transversales.

C-01 implementa get_db.
C-03 (auth-jwt-2fa) implementa get_current_user:
  - Extrae el JWT del header Authorization: Bearer <token>
  - Verifica firma y expiración con core/security.py
  - Resuelve el User desde la DB (via UserRepository)
  - Garantiza: identidad SIEMPRE del JWT verificado, NUNCA de parámetros del request

C-04 (rbac) implementará require_permission.

Regla dura #8: identidad SIEMPRE del JWT verificado.
Regla dura #9: tenant_id siempre scoped en los repositories.
"""

from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import verify_token
from app.core.tenancy import get_tenant_id_from_token


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Dependency que provee una sesion async de base de datos por request.

    Garantiza cierre de la sesion al finalizar la request, incluso ante excepcion
    (el finally en get_session() asegura no haya fuga de conexiones al pool).

    Uso en routers:
        @router.get("/foo")
        async def foo(db: DbSession):
            result = await db.execute(...)
    """
    async for session in get_session():
        yield session


# Alias tipado para usar en type hints de los routers
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Bearer extractor — lee el token del header Authorization
_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Dependency que resuelve el usuario autenticado desde el JWT verificado.

    Flujo:
      1. Extrae el token del header Authorization: Bearer <token>
      2. Verifica firma y expiración con core/security.verify_token()
      3. Extrae user_id y tenant_id del payload (NUNCA de parámetros del request)
      4. Busca el User en la DB via UserRepository
      5. Verifica que el usuario existe y está activo

    Returns:
        Instancia User del usuario autenticado.

    Raises:
        401 Unauthorized: Si el token es inválido, expirado o el usuario no existe.
        403 Forbidden: Si el usuario está desactivado.

    REGLA DURA #8: identidad SIEMPRE del JWT verificado.
    Nunca leer user_id de URL, body, headers arbitrarios ni ningún otro parámetro.
    """
    from app.models.user import User
    from app.repositories.user_repository import UserRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    # Extraer user_id del claim 'sub' — NUNCA de parámetros del request
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise credentials_exception

    # Verificar que el tipo de token es 'access' (no pre_auth ni refresh)
    token_type = payload.get("type", "access")
    if token_type != "access":
        raise credentials_exception

    try:
        user_id = UUID(str(user_id_raw))
    except (ValueError, AttributeError):
        raise credentials_exception

    # Extraer tenant_id del JWT — NUNCA de parámetros del request
    try:
        tenant_id = get_tenant_id_from_token(payload)
    except ValueError:
        raise credentials_exception

    # Buscar usuario en DB con scope de tenant
    repo = UserRepository(db, tenant_id=tenant_id)
    user: User | None = await repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return user


# ---------------------------------------------------------------------------
# SLOTS RESERVADOS para C-04
# ---------------------------------------------------------------------------

# require_permission(module, action): verifica que el usuario tiene el permiso
#   "<module>:<action>" segun la matriz RBAC del tenant.
#   RESERVADO → C-04 (RBAC fino). Fail-closed: sin permiso explicito → 403.
