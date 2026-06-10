"""Repository para la entidad Carrera.

Extiende BaseRepository[Carrera] con `update_estado` específico.
Todos los queries tienen scope de tenant garantizado por BaseRepository.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    """Repository de Carrera con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Carrera)

    async def update_estado(self, id: UUID, estado: str) -> Carrera | None:
        """Cambia el estado de una carrera. Retorna None si no existe en el tenant."""
        carrera = await self.get_by_id(id)
        if carrera is None:
            return None
        carrera.estado = estado
        return await self.update(carrera)
