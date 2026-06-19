"""Repository para LoteComunicacion y Comunicacion (C-12)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import (
    MSG_ENVIADO,
    MSG_ENVIANDO,
    MSG_ERROR,
    MSG_CANCELADO,
    MSG_PENDIENTE,
    Comunicacion,
)
from app.models.lote_comunicacion import (
    LOTE_APROBADO,
    LOTE_CANCELADO,
    LOTE_COMPLETADO,
    LOTE_DESPACHANDO,
    LOTE_PENDIENTE,
    LOTE_PENDIENTE_APROBACION,
    LoteComunicacion,
)
from app.repositories.base import BaseRepository

_BATCH_SIZE = 500


class ComunicacionRepository(BaseRepository[LoteComunicacion]):

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=LoteComunicacion)

    # ------------------------------------------------------------------
    # Lotes
    # ------------------------------------------------------------------

    async def create_lote(self, lote: LoteComunicacion) -> LoteComunicacion:
        lote.tenant_id = self._tenant_id
        self._session.add(lote)
        await self._session.flush()
        await self._session.refresh(lote)
        return lote

    async def get_lote(self, lote_id: UUID) -> LoteComunicacion | None:
        stmt = self._base_query().where(LoteComunicacion.id == lote_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_lotes(self, limit: int = 50, offset: int = 0) -> list[LoteComunicacion]:
        stmt = (
            self._base_query()
            .order_by(LoteComunicacion.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_lote_estado(self, lote_id: UUID, estado: str) -> LoteComunicacion | None:
        lote = await self.get_lote(lote_id)
        if lote is None:
            return None
        lote.estado = estado
        lote.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return lote

    async def marcar_lote_aprobado(
        self, lote_id: UUID, aprobado_por: UUID
    ) -> LoteComunicacion | None:
        lote = await self.get_lote(lote_id)
        if lote is None:
            return None
        now = datetime.now(timezone.utc)
        lote.estado = LOTE_APROBADO
        lote.aprobado_por = aprobado_por
        lote.aprobado_at = now
        lote.updated_at = now
        await self._session.flush()
        return lote

    async def incrementar_contadores(
        self, lote_id: UUID, *, enviados_delta: int = 0, errores_delta: int = 0
    ) -> None:
        lote = await self.get_lote(lote_id)
        if lote is None:
            return
        lote.enviados = (lote.enviados or 0) + enviados_delta
        lote.errores = (lote.errores or 0) + errores_delta
        lote.updated_at = datetime.now(timezone.utc)
        total = (lote.enviados or 0) + (lote.errores or 0)
        if total >= (lote.total_mensajes or 0) and (lote.total_mensajes or 0) > 0:
            lote.estado = LOTE_COMPLETADO
        await self._session.flush()

    # ------------------------------------------------------------------
    # Mensajes individuales
    # ------------------------------------------------------------------

    async def create_batch(self, mensajes: list[Comunicacion]) -> int:
        """Inserta mensajes en lotes de 500. Retorna total insertado."""
        total = 0
        for i in range(0, len(mensajes), _BATCH_SIZE):
            batch = mensajes[i : i + _BATCH_SIZE]
            for m in batch:
                m.tenant_id = self._tenant_id
                self._session.add(m)
            await self._session.flush()
            total += len(batch)
        return total

    async def get_pendientes_despachables(self, limit: int = 50) -> list[Comunicacion]:
        """Mensajes listos para despacho: Pendiente en lotes Pendiente o Aprobado."""
        stmt = (
            select(Comunicacion)
            .join(LoteComunicacion, Comunicacion.lote_id == LoteComunicacion.id)
            .where(Comunicacion.tenant_id == self._tenant_id)
            .where(Comunicacion.deleted_at.is_(None))
            .where(Comunicacion.estado == MSG_PENDIENTE)
            .where(
                LoteComunicacion.estado.in_([LOTE_PENDIENTE, LOTE_APROBADO, LOTE_DESPACHANDO])
            )
            .where(
                # Lotes que no requieren aprobación, o que ya fueron aprobados
                (LoteComunicacion.requiere_aprobacion.is_(False))
                | (LoteComunicacion.aprobado_at.isnot(None))
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def marcar_enviando(self, comunicacion_id: UUID) -> None:
        stmt = select(Comunicacion).where(Comunicacion.id == comunicacion_id)
        result = await self._session.execute(stmt)
        c = result.scalar_one_or_none()
        if c:
            c.estado = MSG_ENVIANDO
            c.updated_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def marcar_enviado(self, comunicacion_id: UUID) -> None:
        stmt = select(Comunicacion).where(Comunicacion.id == comunicacion_id)
        result = await self._session.execute(stmt)
        c = result.scalar_one_or_none()
        if c:
            now = datetime.now(timezone.utc)
            c.estado = MSG_ENVIADO
            c.enviado_at = now
            c.updated_at = now
            await self._session.flush()

    async def marcar_error(self, comunicacion_id: UUID) -> None:
        stmt = select(Comunicacion).where(Comunicacion.id == comunicacion_id)
        result = await self._session.execute(stmt)
        c = result.scalar_one_or_none()
        if c:
            c.estado = MSG_ERROR
            c.updated_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def list_mis_mensajes(self, ep_ids: list[UUID], limit: int = 50) -> list[Comunicacion]:
        """Mensajes recibidos cuyo entrada_padron_id está en ep_ids."""
        if not ep_ids:
            return []
        stmt = (
            select(Comunicacion)
            .where(Comunicacion.tenant_id == self._tenant_id)
            .where(Comunicacion.deleted_at.is_(None))
            .where(Comunicacion.entrada_padron_id.in_(ep_ids))
            .order_by(Comunicacion.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def cancelar_por_lote(self, lote_id: UUID) -> int:
        """Cancela todos los mensajes Pendiente de un lote. Retorna count."""
        stmt = (
            select(Comunicacion)
            .where(Comunicacion.tenant_id == self._tenant_id)
            .where(Comunicacion.lote_id == lote_id)
            .where(Comunicacion.deleted_at.is_(None))
            .where(Comunicacion.estado == MSG_PENDIENTE)
        )
        result = await self._session.execute(stmt)
        items = result.scalars().all()
        now = datetime.now(timezone.utc)
        for item in items:
            item.estado = MSG_CANCELADO
            item.updated_at = now
        await self._session.flush()
        return len(items)
