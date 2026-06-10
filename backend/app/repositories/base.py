"""Repository base generico con scope de tenant obligatorio.

BaseRepository[T] encapsula todas las operaciones CRUD contra SQLAlchemy
async. Garantiza que NINGUN query se ejecuta sin el filtro de tenant.

Regla critica (CLAUDE.md #9):
  Un query sin scope de tenant es un bug que falla en code review.

Decision D4 del design:
  tenant_id se pasa explicitamente en __init__ — no desde ContextVar.
  Esto hace el scope visible y testeable.

Decision D5 del design:
  Soft delete: todos los queries de lectura incluyen `deleted_at IS NULL`.
  No existe metodo hard_delete() ni get_all_without_tenant().

Uso:
    repo = BaseRepository(session, tenant_id=uuid_del_tenant, model=MiModelo)
    item = await repo.get_by_id(some_uuid)
    items = await repo.list(offset=0, limit=20)
    nuevo = await repo.create(MiModelo(field="valor"))
    actualizado = await repo.update(item)
    ok = await repo.soft_delete(item.id)
"""

from datetime import datetime, timezone
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import TenantScopedBase

# Tipo generico T acotado a modelos que hereden TenantScopedBase
T = TypeVar("T", bound=TenantScopedBase)


class BaseRepository(Generic[T]):
    """Repository generico con scope de tenant siempre activo.

    Todos los metodos de consulta filtran por:
      - tenant_id = self.tenant_id   (aislamiento multi-tenant)
      - deleted_at IS NULL           (soft delete transparente)

    Args:
        session:   AsyncSession de SQLAlchemy para la request actual.
        tenant_id: UUID del tenant propietario — obligatorio, sin excepcion.
        model:     Clase del modelo ORM (subclase de TenantScopedBase).
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        model: type[T],
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._model = model

    # ------------------------------------------------------------------
    # Helpers privados — aplicar scope de tenant a cualquier query
    # ------------------------------------------------------------------

    def _base_query(self):
        """SELECT base con filtros de tenant y soft-delete aplicados."""
        return (
            select(self._model)
            .where(self._model.tenant_id == self._tenant_id)
            .where(self._model.deleted_at.is_(None))
        )

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    async def get_by_id(self, id: UUID) -> T | None:
        """Retorna el registro con el id dado, o None si no existe o no pertenece al tenant.

        El filtro de tenant es transparente: el llamador ve None (no un error 403).
        """
        stmt = self._base_query().where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Retorna los registros activos del tenant, paginados.

        Args:
            offset: Numero de registros a saltar (paginacion).
            limit:  Maximo de registros a retornar.

        Returns:
            Lista de instancias del modelo (puede estar vacia).
        """
        stmt = self._base_query().offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    async def create(self, obj: T) -> T:
        """Persiste un nuevo objeto, inyectando tenant_id si no estaba seteado.

        Args:
            obj: Instancia del modelo a persistir.

        Returns:
            El mismo objeto con id y timestamps populados.
        """
        # Inyectar tenant_id siempre — nunca confiar en que el llamador lo seteara
        obj.tenant_id = self._tenant_id

        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        """Persiste los cambios en un objeto existente.

        Args:
            obj: Instancia modificada del modelo.

        Returns:
            El objeto actualizado (misma referencia).
        """
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def soft_delete(self, id: UUID) -> bool:
        """Marca el registro como eliminado (soft delete).

        Setea deleted_at = now(UTC). El registro permanece en la BD para
        auditoria (regla dura #13: append-only).

        Args:
            id: UUID del registro a eliminar.

        Returns:
            True si el registro existia y fue marcado.
            False si no existia o no pertenece al tenant (sin levantar excepcion).
        """
        obj = await self.get_by_id(id)
        if obj is None:
            return False

        obj.deleted_at = datetime.now(timezone.utc)
        self._session.add(obj)
        await self._session.flush()
        return True
