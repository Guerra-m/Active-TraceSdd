import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.base import BaseRepository


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=InstanciaEncuentro)

    async def list_filtrado(
        self,
        *,
        materia_id: UUID | None = None,
        estado: str | None = None,
        fecha_desde: datetime.date | None = None,
        fecha_hasta: datetime.date | None = None,
    ) -> list[InstanciaEncuentro]:
        stmt = self._base_query()
        if materia_id is not None:
            stmt = stmt.where(InstanciaEncuentro.materia_id == materia_id)
        if estado is not None:
            stmt = stmt.where(InstanciaEncuentro.estado == estado)
        if fecha_desde is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha <= fecha_hasta)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_para_html(
        self,
        *,
        materia_id: UUID | None = None,
        slot_id: UUID | None = None,
    ) -> list[InstanciaEncuentro]:
        """Instancias no canceladas ordenadas por fecha+hora ASC (para el bloque HTML)."""
        stmt = (
            self._base_query()
            .where(InstanciaEncuentro.estado != "Cancelado")
            .order_by(InstanciaEncuentro.fecha.asc(), InstanciaEncuentro.hora.asc())
        )
        if materia_id is not None:
            stmt = stmt.where(InstanciaEncuentro.materia_id == materia_id)
        if slot_id is not None:
            stmt = stmt.where(InstanciaEncuentro.slot_id == slot_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
