"""Repository para la tabla RolPermiso.

Consulta los permisos asignados a un rol dentro de un tenant.
Incluye la matriz base del sistema (tenant_id=NULL) + overrides del tenant.

La resolución de permisos efectivos usa este repository para obtener
los permisos de cada rol que tiene el usuario.
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso


class RolPermisoRepository:
    """Repository de asignaciones rol↔permiso, con scope de tenant."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_permisos_for_rol(
        self, rol_id: UUID
    ) -> list[tuple[str, bool]]:
        """Retorna lista de (permiso_code, is_own_resource) para el rol dado.

        Incluye permisos del sistema (tenant_id=NULL) y overrides del tenant.
        Si el mismo permiso existe con is_own_resource=True (sistema) y
        is_own_resource=False (tenant override), el caller (RbacService)
        aplica la regla "global prevalece".

        Args:
            rol_id: UUID del rol.

        Returns:
            Lista de tuplas (permiso_code, is_own_resource).
        """
        stmt = (
            select(Permiso.code, RolPermiso.is_own_resource)
            .join(Permiso, RolPermiso.permiso_id == Permiso.id)
            .where(RolPermiso.rol_id == rol_id)
            .where(
                or_(
                    RolPermiso.tenant_id.is_(None),
                    RolPermiso.tenant_id == self._tenant_id,
                )
            )
            .where(RolPermiso.deleted_at.is_(None))
            .where(Permiso.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        return [(row.code, row.is_own_resource) for row in result]
