"""Repository para FechaAcademica y ProgramaMateria (C-17)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import FechaAcademica, ProgramaMateria
from app.repositories.base import BaseRepository


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=FechaAcademica)

    async def list_filtrado(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
        tipo: str | None = None,
    ) -> list[FechaAcademica]:
        stmt = self._base_query()
        if materia_id is not None:
            stmt = stmt.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(FechaAcademica.cohorte_id == cohorte_id)
        if periodo is not None:
            stmt = stmt.where(FechaAcademica.periodo == periodo)
        if tipo is not None:
            stmt = stmt.where(FechaAcademica.tipo == tipo)
        stmt = stmt.order_by(FechaAcademica.fecha.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=ProgramaMateria)

    async def list_filtrado(
        self,
        *,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[ProgramaMateria]:
        stmt = self._base_query()
        if materia_id is not None:
            stmt = stmt.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(ProgramaMateria.cohorte_id == cohorte_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
