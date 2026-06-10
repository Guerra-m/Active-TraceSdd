"""Repository para EntradaPadron (C-09 padron-ingesta-moodle).

Extiende BaseRepository[EntradaPadron] con:
  - create_batch: inserta entradas en lotes de 500 para evitar memory pressure
  - list_by_version: lista entradas de una versión específica

Todos los queries tienen scope de tenant garantizado por BaseRepository.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrada_padron import EntradaPadron
from app.repositories.base import BaseRepository

_BATCH_SIZE = 500


class EntradaPadronRepository(BaseRepository[EntradaPadron]):
    """Repository de EntradaPadron con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=EntradaPadron)

    async def create_batch(self, entradas: list[EntradaPadron]) -> int:
        """Inserta entradas en lotes de 500. Retorna cantidad total insertada."""
        total = 0
        for i in range(0, len(entradas), _BATCH_SIZE):
            batch = entradas[i : i + _BATCH_SIZE]
            for entrada in batch:
                entrada.tenant_id = self._tenant_id
                self._session.add(entrada)
            await self._session.flush()
            total += len(batch)
        return total

    async def list_by_version(self, version_id: UUID) -> list[EntradaPadron]:
        """Lista todas las entradas de una versión específica del tenant."""
        stmt = (
            self._base_query()
            .where(EntradaPadron.version_id == version_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
