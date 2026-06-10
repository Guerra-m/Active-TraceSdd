"""Worker de despacho de comunicaciones — C-12.

Corre como asyncio.Task en el lifespan de la app. Pollea la DB cada
`poll_interval_s` segundos, toma mensajes despachables y los envía
usando el EmailSender configurado (stub en dev, SMTP en prod).

Máquina de estados (RN-15):
  Pendiente → Enviando → Enviado | Error
  Pendiente → Cancelado (por cancelación del lote — no tarea del worker)
"""

import asyncio
import logging

from app.integrations.email_sender import AbstractEmailSender
from app.models.lote_comunicacion import LOTE_DESPACHANDO

logger = logging.getLogger(__name__)


class ComunicacionWorker:
    """Procesa mensajes pendientes despachables de forma continua."""

    def __init__(
        self,
        db_factory,
        sender: AbstractEmailSender,
        poll_interval_s: float = 10.0,
    ) -> None:
        self._db_factory = db_factory
        self._sender = sender
        self._poll_interval_s = poll_interval_s
        self._running = False

    async def loop(self) -> None:
        """Bucle principal del worker. Llamar via asyncio.create_task()."""
        self._running = True
        logger.info("ComunicacionWorker iniciado", extra={"poll_interval_s": self._poll_interval_s})
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("Error inesperado en ComunicacionWorker._tick")
            await asyncio.sleep(self._poll_interval_s)

    def stop(self) -> None:
        self._running = False

    async def _tick(self) -> None:
        """Una iteración: obtiene mensajes despachables y los envía."""
        from app.core.encryption import decrypt
        from app.repositories.comunicacion_repository import ComunicacionRepository

        async with self._db_factory() as session:
            # Usar un tenant_id sentinel para la query cross-tenant (el repo filtra por tenant)
            # El worker opera a nivel global: necesitamos todos los mensajes pendientes
            from sqlalchemy import select
            from app.models.comunicacion import Comunicacion, MSG_PENDIENTE, MSG_ENVIANDO
            from app.models.lote_comunicacion import LoteComunicacion, LOTE_PENDIENTE, LOTE_APROBADO

            stmt = (
                select(Comunicacion)
                .join(LoteComunicacion, Comunicacion.lote_id == LoteComunicacion.id)
                .where(Comunicacion.deleted_at.is_(None))
                .where(Comunicacion.estado == MSG_PENDIENTE)
                .where(LoteComunicacion.estado.in_([LOTE_PENDIENTE, LOTE_APROBADO, LOTE_DESPACHANDO]))
                .where(
                    (LoteComunicacion.requiere_aprobacion.is_(False))
                    | (LoteComunicacion.aprobado_at.isnot(None))
                )
                .limit(50)
            )
            result = await session.execute(stmt)
            mensajes = result.scalars().all()

            if not mensajes:
                return

            logger.debug("Worker: procesando %d mensajes", len(mensajes))

            # Agrupar lote IDs únicos para actualizar estado a Despachando
            lote_ids = {m.lote_id for m in mensajes}
            for lote_id in lote_ids:
                lote_stmt = select(LoteComunicacion).where(LoteComunicacion.id == lote_id)
                lote_result = await session.execute(lote_stmt)
                lote = lote_result.scalar_one_or_none()
                if lote and lote.estado in (LOTE_PENDIENTE, LOTE_APROBADO):
                    lote.estado = LOTE_DESPACHANDO
                    await session.flush()

            enviados = 0
            errores = 0
            lote_enviados: dict = {}
            lote_errores: dict = {}

            for msg in mensajes:
                await self._despachar(session, msg, decrypt, lote_enviados, lote_errores)

            # Actualizar contadores de lotes
            from datetime import datetime, timezone
            from app.models.lote_comunicacion import LOTE_COMPLETADO

            for lote_id in lote_ids:
                lote_stmt = select(LoteComunicacion).where(LoteComunicacion.id == lote_id)
                lote_result = await session.execute(lote_stmt)
                lote = lote_result.scalar_one_or_none()
                if lote is None:
                    continue
                delta_env = lote_enviados.get(lote_id, 0)
                delta_err = lote_errores.get(lote_id, 0)
                lote.enviados = (lote.enviados or 0) + delta_env
                lote.errores = (lote.errores or 0) + delta_err
                lote.updated_at = datetime.now(timezone.utc)
                total_terminados = (lote.enviados or 0) + (lote.errores or 0)
                if total_terminados >= (lote.total_mensajes or 0) and (lote.total_mensajes or 0) > 0:
                    lote.estado = LOTE_COMPLETADO
                await session.flush()

            await session.commit()

    async def _despachar(self, session, msg, decrypt, lote_enviados: dict, lote_errores: dict) -> None:
        from datetime import datetime, timezone
        from app.models.comunicacion import MSG_ENVIANDO, MSG_ENVIADO, MSG_ERROR

        msg.estado = MSG_ENVIANDO
        await session.flush()

        try:
            email_to = decrypt(msg.destinatario)
            await self._sender.send(email_to, msg.asunto, msg.cuerpo)
            now = datetime.now(timezone.utc)
            msg.estado = MSG_ENVIADO
            msg.enviado_at = now
            msg.updated_at = now
            lote_enviados[msg.lote_id] = lote_enviados.get(msg.lote_id, 0) + 1
            logger.debug("Mensaje enviado: %s", msg.id)
        except Exception:
            msg.estado = MSG_ERROR
            msg.updated_at = datetime.now(timezone.utc)
            lote_errores[msg.lote_id] = lote_errores.get(msg.lote_id, 0) + 1
            logger.exception("Error al despachar mensaje %s", msg.id)

        await session.flush()
