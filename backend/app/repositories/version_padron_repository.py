"""Repository para VersionPadron (C-09 padron-ingesta-moodle).

Extiende BaseRepository[VersionPadron] con operaciones específicas:
  - get_activa: obtiene la versión activa para una materia×cohorte
  - desactivar: marca activa=False en una versión (sin borrarla)

Todos los queries tienen scope de tenant garantizado por BaseRepository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.version_padron import VersionPadron
from app.repositories.base import BaseRepository


class VersionPadronRepository(BaseRepository[VersionPadron]):
    """Repository de VersionPadron con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=VersionPadron)

    async def get_activa(self, materia_id: UUID, cohorte_id: UUID) -> VersionPadron | None:
        """Retorna la versión activa para materia×cohorte del tenant, o None."""
        stmt = (
            self._base_query()
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.activa.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def desactivar(self, version: VersionPadron) -> VersionPadron:
        """Marca la versión como inactiva (activa=False). No la borra."""
        version.activa = False
        return await self.update(version)
