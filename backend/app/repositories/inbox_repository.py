"""Repository para HiloMensaje y MensajeInterno (C-20)."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.repositories.base import BaseRepository


class HiloMensajeRepository(BaseRepository[HiloMensaje]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=HiloMensaje)

    async def list_para_usuario(self, user_id: UUID) -> list[HiloMensaje]:
        """Hilos donde el usuario es remitente o destinatario, ordenados por created_at DESC."""
        stmt = (
            self._base_query()
            .where(
                or_(
                    HiloMensaje.remitente_id == user_id,
                    HiloMensaje.destinatario_id == user_id,
                )
            )
            .order_by(HiloMensaje.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class MensajeInternoRepository(BaseRepository[MensajeInterno]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=MensajeInterno)

    async def list_by_hilo(self, hilo_id: UUID) -> list[MensajeInterno]:
        """Mensajes de un hilo ordenados por created_at ASC."""
        stmt = (
            self._base_query()
            .where(MensajeInterno.hilo_id == hilo_id)
            .order_by(MensajeInterno.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
