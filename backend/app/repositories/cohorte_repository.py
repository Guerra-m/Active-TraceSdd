"""Repository para la entidad Cohorte.

Extiende BaseRepository[Cohorte]. Incluye `list_by_carrera` para filtrar
cohortes de una carrera específica dentro del tenant.
Todos los queries tienen scope de tenant garantizado por BaseRepository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohorte import Cohorte
from app.repositories.base import BaseRepository


class CohorteRepository(BaseRepository[Cohorte]):
    """Repository de Cohorte con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Cohorte)

    async def list_by_carrera(self, carrera_id: UUID) -> list[Cohorte]:
        """Lista cohortes activas de una carrera dentro del tenant."""
        stmt = (
            self._base_query()
            .where(Cohorte.carrera_id == carrera_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
