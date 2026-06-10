"""Repository para Calificacion (C-10 calificaciones-y-umbral)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.repositories.base import BaseRepository

_BATCH_SIZE = 500


class CalificacionRepository(BaseRepository[Calificacion]):

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Calificacion)

    async def create_batch(self, calificaciones: list[Calificacion]) -> int:
        """Inserta calificaciones en lotes de 500. Retorna total insertado."""
        total = 0
        for i in range(0, len(calificaciones), _BATCH_SIZE):
            batch = calificaciones[i : i + _BATCH_SIZE]
            for c in batch:
                c.tenant_id = self._tenant_id
                self._session.add(c)
            await self._session.flush()
            total += len(batch)
        return total

    async def delete_by_asignacion_materia(
        self, asignacion_id: UUID, materia_id: UUID
    ) -> int:
        """Soft-delete de todas las calificaciones de esa asignación × materia."""
        stmt = (
            self._base_query()
            .where(Calificacion.asignacion_id == asignacion_id)
            .where(Calificacion.materia_id == materia_id)
        )
        result = await self._session.execute(stmt)
        items = result.scalars().all()
        now = datetime.now(timezone.utc)
        for item in items:
            item.deleted_at = now
        await self._session.flush()
        return len(items)

    async def list_by_asignacion_materia(
        self, asignacion_id: UUID, materia_id: UUID
    ) -> list[Calificacion]:
        stmt = (
            self._base_query()
            .where(Calificacion.asignacion_id == asignacion_id)
            .where(Calificacion.materia_id == materia_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
