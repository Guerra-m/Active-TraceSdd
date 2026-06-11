from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=SlotEncuentro)

    async def list_filtrado(
        self,
        *,
        materia_id: UUID | None = None,
        asignacion_id: UUID | None = None,
    ) -> list[SlotEncuentro]:
        stmt = self._base_query()
        if materia_id is not None:
            stmt = stmt.where(SlotEncuentro.materia_id == materia_id)
        if asignacion_id is not None:
            stmt = stmt.where(SlotEncuentro.asignacion_id == asignacion_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
