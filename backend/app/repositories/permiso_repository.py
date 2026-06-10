"""Repository para la entidad Permiso.

Los permisos son globales (sin tenant). Este repository no filtra por tenant_id
ya que los permisos pertenecen al catálogo global del sistema.

Uso:
    repo = PermisoRepository(session)
    perm = await repo.get_by_code("calificaciones:importar")
    all_perms = await repo.list_active()
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso


class PermisoRepository:
    """Repository de permisos del catálogo global."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: str) -> Permiso | None:
        """Retorna el permiso con el code dado, o None si no existe."""
        stmt = (
            select(Permiso)
            .where(Permiso.code == code)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, permiso_id: UUID) -> Permiso | None:
        """Retorna el permiso con el id dado, o None si no existe."""
        stmt = (
            select(Permiso)
            .where(Permiso.id == permiso_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Permiso]:
        """Retorna todos los permisos activos del catálogo."""
        stmt = (
            select(Permiso)
            .where(Permiso.is_active.is_(True))
            .order_by(Permiso.code)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
