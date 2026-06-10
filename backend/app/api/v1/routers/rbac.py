"""Router de catálogo RBAC — endpoints de consulta (GET only).

Endpoints:
  GET /rbac/roles            → lista de roles activos del tenant + sistema
  GET /rbac/roles/{rol_id}/permisos → permisos del rol con is_own_resource

Todos los endpoints están protegidos con require_permission("roles:ver").
Solo usuarios con el permiso roles:ver (e.g. ADMIN) pueden consultar el catálogo.

Flujo (regla #11):
  Router → Service/Repository → Models
  (nunca lógica de negocio en el router)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.repositories.permiso_repository import PermisoRepository
from app.repositories.rol_permiso_repository import RolPermisoRepository
from app.repositories.rol_repository import RolRepository
from app.schemas.rbac import PermisoResponse, RolPermisoResponse, RolResponse

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get(
    "/roles",
    response_model=list[RolResponse],
    summary="Listar roles disponibles (sistema + custom del tenant)",
)
async def list_roles(
    request: Request,
    _: None = Depends(require_permission("roles:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RolResponse]:
    """Retorna los roles activos del sistema y del tenant del usuario.

    Requiere permiso: `roles:ver`
    """
    repo = RolRepository(db, tenant_id=current_user.tenant_id)
    roles = await repo.list_active(include_system=True)
    return [RolResponse.model_validate(r) for r in roles]


@router.get(
    "/roles/{rol_id}/permisos",
    response_model=list[RolPermisoResponse],
    summary="Listar permisos de un rol con flag is_own_resource",
)
async def list_rol_permisos(
    rol_id: UUID,
    request: Request,
    _: None = Depends(require_permission("roles:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RolPermisoResponse]:
    """Retorna los permisos asignados al rol, con su flag is_own_resource.

    Requiere permiso: `roles:ver`
    """
    # Verificar que el rol existe y es accesible para el tenant
    rol_repo = RolRepository(db, tenant_id=current_user.tenant_id)
    rol = await rol_repo.get_by_id(rol_id)
    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol {rol_id} no encontrado",
        )

    rp_repo = RolPermisoRepository(db, tenant_id=current_user.tenant_id)
    perm_codes = await rp_repo.get_permisos_for_rol(rol_id)

    # Enriquecer con los objetos Permiso completos
    perm_repo = PermisoRepository(db)
    result = []
    for code, is_own in perm_codes:
        perm_obj = await perm_repo.get_by_code(code)
        if perm_obj is not None:
            result.append(
                RolPermisoResponse(
                    permiso=PermisoResponse.model_validate(perm_obj),
                    is_own_resource=is_own,
                )
            )

    return result
