"""Repository para la entidad Rol.

Acceso a roles del dominio (is_system=True, tenant_id=NULL) y roles custom
del tenant actual. Nunca expone roles de otros tenants.

Regla: un query sin scope de tenant es un bug. Por eso:
  - list_active() incluye roles sistema (tenant_id IS NULL) SIEMPRE
  - list_active() incluye roles custom del tenant (tenant_id = self._tenant_id)
  - get_by_code() busca en ambos conjuntos
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rol import Rol


class RolRepository:
    """Repository de roles — sistema y custom del tenant."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _tenant_scoped_filter(self):
        """Filtro que incluye roles sistema (NULL) y roles del tenant actual."""
        return or_(
            Rol.tenant_id.is_(None),
            Rol.tenant_id == self._tenant_id,
        )

    async def get_by_code(self, code: str) -> Rol | None:
        """Retorna el rol con el code dado (sistema o del tenant), o None."""
        stmt = (
            select(Rol)
            .where(self._tenant_scoped_filter())
            .where(Rol.code == code)
            .where(Rol.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, rol_id: UUID) -> Rol | None:
        """Retorna el rol con el id dado (sistema o del tenant), o None."""
        stmt = (
            select(Rol)
            .where(self._tenant_scoped_filter())
            .where(Rol.id == rol_id)
            .where(Rol.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, include_system: bool = True) -> list[Rol]:
        """Retorna roles activos del tenant + roles sistema si include_system=True."""
        if include_system:
            scope_filter = self._tenant_scoped_filter()
        else:
            scope_filter = Rol.tenant_id == self._tenant_id

        stmt = (
            select(Rol)
            .where(scope_filter)
            .where(Rol.is_active.is_(True))
            .where(Rol.deleted_at.is_(None))
            .order_by(Rol.code)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
