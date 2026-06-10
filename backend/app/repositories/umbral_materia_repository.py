"""Repository para UmbralMateria (C-10 calificaciones-y-umbral)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.umbral_materia import UmbralMateria
from app.repositories.base import BaseRepository


class UmbralMateriaRepository(BaseRepository[UmbralMateria]):

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=UmbralMateria)

    async def get_by_asignacion_materia(
        self, asignacion_id: UUID, materia_id: UUID
    ) -> UmbralMateria | None:
        stmt = (
            self._base_query()
            .where(UmbralMateria.asignacion_id == asignacion_id)
            .where(UmbralMateria.materia_id == materia_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> UmbralMateria:
        existing = await self.get_by_asignacion_materia(asignacion_id, materia_id)
        if existing:
            existing.umbral_pct = umbral_pct
            existing.valores_aprobatorios = valores_aprobatorios
            existing.updated_at = datetime.now(timezone.utc)
            return await self.update(existing)
        nuevo = UmbralMateria(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        nuevo.tenant_id = self._tenant_id
        self._session.add(nuevo)
        await self._session.flush()
        await self._session.refresh(nuevo)
        return nuevo
