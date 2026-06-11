from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia
from app.repositories.base import BaseRepository


class GuardiaRepository(BaseRepository[Guardia]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Guardia)

    async def list_filtrado(
        self,
        *,
        materia_id: UUID | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
        solo_tenant: bool = True,
    ) -> list[Guardia]:
        """Lista guardias del tenant con filtros opcionales.

        solo_tenant=True → devuelve todas las del tenant.
        asignacion_id → filtra por tutor específico.
        """
        stmt = self._base_query()
        if materia_id is not None:
            stmt = stmt.where(Guardia.materia_id == materia_id)
        if estado is not None:
            stmt = stmt.where(Guardia.estado == estado)
        if not solo_tenant and asignacion_id is not None:
            stmt = stmt.where(Guardia.asignacion_id == asignacion_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
