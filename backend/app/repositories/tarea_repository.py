"""Repository para Tarea y ComentarioTarea (C-16)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.base import BaseRepository


class TareaRepository(BaseRepository[Tarea]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Tarea)

    async def list_filtrado(
        self,
        *,
        asignado_a: UUID | None = None,
        estado: str | None = None,
        materia_id: UUID | None = None,
    ) -> list[Tarea]:
        stmt = self._base_query()
        if asignado_a is not None:
            stmt = stmt.where(Tarea.asignado_a == asignado_a)
        if estado is not None:
            stmt = stmt.where(Tarea.estado == estado)
        if materia_id is not None:
            stmt = stmt.where(Tarea.materia_id == materia_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ComentarioTareaRepository(BaseRepository[ComentarioTarea]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=ComentarioTarea)

    async def list_by_tarea(self, tarea_id: UUID) -> list[ComentarioTarea]:
        stmt = (
            self._base_query()
            .where(ComentarioTarea.tarea_id == tarea_id)
            .order_by(ComentarioTarea.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
