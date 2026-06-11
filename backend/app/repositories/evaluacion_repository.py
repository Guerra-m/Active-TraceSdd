"""Repository para Evaluacion, ReservaEvaluacion y ResultadoEvaluacion (C-14)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Evaluacion)


class ReservaEvaluacionRepository(BaseRepository[ReservaEvaluacion]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=ReservaEvaluacion)

    async def count_activas(self, evaluacion_id: UUID) -> int:
        """Cuenta reservas activas para validar disponibilidad de cupo."""
        stmt = (
            select(func.count())
            .select_from(ReservaEvaluacion)
            .where(ReservaEvaluacion.tenant_id == self._tenant_id)
            .where(ReservaEvaluacion.deleted_at.is_(None))
            .where(ReservaEvaluacion.evaluacion_id == evaluacion_id)
            .where(ReservaEvaluacion.estado == "Activa")
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_by_evaluacion(self, evaluacion_id: UUID) -> list[ReservaEvaluacion]:
        stmt = (
            self._base_query()
            .where(ReservaEvaluacion.evaluacion_id == evaluacion_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_alumno_evaluacion(self, *, alumno_id: UUID, evaluacion_id: UUID) -> ReservaEvaluacion | None:
        stmt = (
            self._base_query()
            .where(ReservaEvaluacion.alumno_id == alumno_id)
            .where(ReservaEvaluacion.evaluacion_id == evaluacion_id)
            .where(ReservaEvaluacion.estado == "Activa")
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class ResultadoEvaluacionRepository(BaseRepository[ResultadoEvaluacion]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=ResultadoEvaluacion)

    async def list_by_evaluacion(self, evaluacion_id: UUID) -> list[ResultadoEvaluacion]:
        stmt = (
            self._base_query()
            .where(ResultadoEvaluacion.evaluacion_id == evaluacion_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_alumno_evaluacion(self, *, alumno_id: UUID, evaluacion_id: UUID) -> ResultadoEvaluacion | None:
        stmt = (
            self._base_query()
            .where(ResultadoEvaluacion.alumno_id == alumno_id)
            .where(ResultadoEvaluacion.evaluacion_id == evaluacion_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_con_nota(self, evaluacion_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ResultadoEvaluacion)
            .where(ResultadoEvaluacion.tenant_id == self._tenant_id)
            .where(ResultadoEvaluacion.deleted_at.is_(None))
            .where(ResultadoEvaluacion.evaluacion_id == evaluacion_id)
            .where(ResultadoEvaluacion.nota_final.isnot(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
