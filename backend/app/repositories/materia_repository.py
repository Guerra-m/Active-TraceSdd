"""Repository para la entidad Materia.

Extiende BaseRepository[Materia] con `update_estado` específico.
Todos los queries tienen scope de tenant garantizado por BaseRepository.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.materia import Materia
from app.repositories.base import BaseRepository


class MateriaRepository(BaseRepository[Materia]):
    """Repository de Materia con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Materia)

    async def update_estado(self, id: UUID, estado: str) -> Materia | None:
        """Cambia el estado de una materia. Retorna None si no existe en el tenant."""
        materia = await self.get_by_id(id)
        if materia is None:
            return None
        materia.estado = estado
        return await self.update(materia)
