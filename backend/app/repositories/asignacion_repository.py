"""Repository para la entidad Asignacion (C-07 usuarios-y-asignaciones).

Extiende BaseRepository[Asignacion] con listado filtrado por atributos opcionales.
Todos los queries tienen scope de tenant garantizado por BaseRepository.

Nota: estado_vigencia es un @property del modelo, calculado en Python.
El repository retorna objetos ORM y el llamador (router/schema) serializa
incluyendo el @property.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Repository de Asignacion con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Asignacion)

    async def list_filtrado(
        self,
        *,
        usuario_id: UUID | None = None,
        rol: str | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Asignacion]:
        """Lista asignaciones del tenant con filtros opcionales acumulables."""
        stmt = self._base_query()

        if usuario_id is not None:
            stmt = stmt.where(Asignacion.usuario_id == usuario_id)
        if rol is not None:
            stmt = stmt.where(Asignacion.rol == rol)
        if materia_id is not None:
            stmt = stmt.where(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Asignacion.cohorte_id == cohorte_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
