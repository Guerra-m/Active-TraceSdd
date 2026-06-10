"""Guard de autorización RBAC — require_permission.

Implementa la dependency FastAPI `require_permission(code: str)` que:
  1. Extrae la identidad del JWT verificado (vía get_current_user).
  2. Llama a RbacService.get_effective_permissions (server-side, siempre DB).
  3. Verifica si el permiso solicitado está en el set efectivo.
  4. Si NO está → raise HTTPException(403, "Permiso insuficiente: <code>").
  5. Cachea el resultado en request.state.rbac_permissions para evitar
     queries redundantes si hay múltiples require_permission en el mismo
     request (Decisión D5).
  6. Expone permission_is_own_resource en request.state cuando el permiso
     existe, para que el Service layer valide propiedad del recurso.

Reglas duras aplicadas:
  - #8: identidad del JWT verificado, nunca de parámetros del request.
  - #10: RBAC fino modulo:accion; fail-closed → 403 sin permiso explícito.
  - Flujo: este módulo llama a RbacService (service); jamás a la DB directamente.

Uso en routers:
    @router.get("/calificaciones")
    async def importar(
        request: Request,
        _: None = Depends(require_permission("calificaciones:importar")),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        is_own = request.state.permission_is_own_resource
        ...
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db


def require_permission(code: str) -> Callable:
    """Factory que retorna una dependency FastAPI para verificar un permiso.

    El permiso debe estar en formato 'modulo:accion'.

    Args:
        code: Código del permiso requerido (e.g. "calificaciones:importar").

    Returns:
        Dependency FastAPI que verifica el permiso y es inyectable con Depends().

    Raises (cuando se ejecuta la dependency):
        401 Unauthorized: Si no hay JWT válido (get_current_user actúa primero).
        403 Forbidden: Si el usuario no tiene el permiso requerido.
    """
    async def _check_permission(
        request: Request,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        """Dependency interna que realiza la verificación de permiso."""
        from app.services.rbac_service import RbacService

        # Obtener tenant_id del usuario (disponible como atributo del modelo User)
        tenant_id = current_user.tenant_id

        # Cache de permisos en request.state — evita queries redundantes
        # si hay múltiples require_permission en el mismo endpoint
        if not hasattr(request.state, "rbac_permissions"):
            permissions = await RbacService.get_effective_permissions(
                user_id=current_user.id,
                tenant_id=tenant_id,
                db=db,
            )
            request.state.rbac_permissions = permissions
        else:
            permissions = request.state.rbac_permissions

        # Verificar si el permiso requerido está en el set efectivo
        # El set contiene tuplas (permiso_code, is_own_resource)
        perm_codes = {perm_code for perm_code, _ in permissions}

        if code not in perm_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso insuficiente: {code}",
            )

        # Exponer is_own_resource en request.state para uso en el Service layer
        is_own = next(
            (is_own for perm_code, is_own in permissions if perm_code == code),
            False,
        )
        request.state.permission_is_own_resource = is_own

        # actor_id ya fue seteado por get_current_user; si por algún motivo
        # la dependency corre sin request (tests unitarios), garantizar el attr.
        if not hasattr(request.state, "actor_id"):
            request.state.actor_id = current_user.id

    return _check_permission
