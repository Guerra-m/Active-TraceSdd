"""Repository para Liquidacion (C-18 liquidaciones-y-honorarios).

Extiende BaseRepository con queries específicos:
  - list_por_periodo: lista liquidaciones filtradas por período y opcionalmente cohorte
  - get_by_usuario_periodo: obtiene liquidación de un usuario en un período/cohorte
  - sum_por_periodo: suma totales para KPIs

Regla dura #9: TODOS los queries filtran por tenant_id.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Repository para Liquidacion con scope de tenant."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Liquidacion)

    async def list_por_periodo(
        self,
        periodo: str,
        *,
        cohorte_id: UUID | None = None,
        offset: int = 0,
        limit: int = 200,
    ) -> list[Liquidacion]:
        """Lista liquidaciones del período con scope de tenant."""
        stmt = (
            self._base_query()
            .where(Liquidacion.periodo == periodo)
        )
        if cohorte_id is not None:
            stmt = stmt.where(Liquidacion.cohorte_id == cohorte_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_usuario_periodo(
        self,
        usuario_id: UUID,
        periodo: str,
        cohorte_id: UUID,
    ) -> Liquidacion | None:
        """Retorna la liquidación de un usuario en un período/cohorte."""
        stmt = (
            self._base_query()
            .where(Liquidacion.usuario_id == usuario_id)
            .where(Liquidacion.periodo == periodo)
            .where(Liquidacion.cohorte_id == cohorte_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def sum_kpis(
        self,
        periodo: str,
        cohorte_id: UUID,
    ) -> dict:
        """Calcula KPIs de liquidaciones para el período y cohorte dados.

        Retorna: total_general, total_nexo, total_facturantes, cantidad_liquidaciones.
        """
        # Query para todas las liquidaciones no excluidas
        stmt_general = (
            select(func.coalesce(func.sum(Liquidacion.total), 0))
            .where(Liquidacion.tenant_id == self._tenant_id)
            .where(Liquidacion.deleted_at.is_(None))
            .where(Liquidacion.periodo == periodo)
            .where(Liquidacion.cohorte_id == cohorte_id)
            .where(Liquidacion.excluido_por_factura.is_(False))
        )
        stmt_nexo = (
            select(func.coalesce(func.sum(Liquidacion.total), 0))
            .where(Liquidacion.tenant_id == self._tenant_id)
            .where(Liquidacion.deleted_at.is_(None))
            .where(Liquidacion.periodo == periodo)
            .where(Liquidacion.cohorte_id == cohorte_id)
            .where(Liquidacion.es_nexo.is_(True))
            .where(Liquidacion.excluido_por_factura.is_(False))
        )
        stmt_facturantes = (
            select(func.coalesce(func.sum(Liquidacion.total), 0))
            .where(Liquidacion.tenant_id == self._tenant_id)
            .where(Liquidacion.deleted_at.is_(None))
            .where(Liquidacion.periodo == periodo)
            .where(Liquidacion.cohorte_id == cohorte_id)
            .where(Liquidacion.excluido_por_factura.is_(True))
        )
        stmt_count = (
            select(func.count())
            .where(Liquidacion.tenant_id == self._tenant_id)
            .where(Liquidacion.deleted_at.is_(None))
            .where(Liquidacion.periodo == periodo)
            .where(Liquidacion.cohorte_id == cohorte_id)
            .where(Liquidacion.excluido_por_factura.is_(False))
        )

        r_general = await self._session.execute(stmt_general)
        r_nexo = await self._session.execute(stmt_nexo)
        r_facturantes = await self._session.execute(stmt_facturantes)
        r_count = await self._session.execute(stmt_count)

        return {
            "total_general": Decimal(str(r_general.scalar() or 0)),
            "total_nexo": Decimal(str(r_nexo.scalar() or 0)),
            "total_facturantes": Decimal(str(r_facturantes.scalar() or 0)),
            "cantidad_liquidaciones": r_count.scalar() or 0,
        }
