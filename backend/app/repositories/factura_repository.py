"""Repository para Factura (C-18 liquidaciones-y-honorarios).

Extiende BaseRepository con queries específicos:
  - list_facturas: lista con filtros de docente, período y estado
  - get_by_id: heredado de BaseRepository

Regla dura #9: TODOS los queries filtran por tenant_id.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Repository para Factura con scope de tenant."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Factura)

    async def list_facturas(
        self,
        *,
        usuario_id: UUID | None = None,
        periodo: str | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Factura]:
        """Lista facturas del tenant con filtros opcionales."""
        stmt = self._base_query()
        if usuario_id is not None:
            stmt = stmt.where(Factura.usuario_id == usuario_id)
        if periodo is not None:
            stmt = stmt.where(Factura.periodo == periodo)
        if estado is not None:
            stmt = stmt.where(Factura.estado == estado)
        stmt = stmt.order_by(Factura.fecha_carga.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
