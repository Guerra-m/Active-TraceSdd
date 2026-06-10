"""Entrypoint del worker de background jobs — active-trace.

PLACEHOLDER: la tecnologia real de la cola (asyncio propio / Celery / ARQ)
se define en ADR-003, que se resuelve al construir el modulo de comunicaciones.

Este modulo expone un entrypoint minimo que el servicio `worker` del
docker-compose puede invocar. En C-01 simplemente arranca un loop no-op
e indica que el worker esta corriendo.

Uso (docker-compose / Easypanel):
    python -m app.workers.main
"""

import asyncio
import logging
import signal

from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Loop principal del worker — no-op hasta que se implemente la cola (ADR-003)."""
    setup_logging()
    logger.info("active-trace worker arrancando (placeholder — ADR-003 pendiente)")

    # Manejar SIGTERM / SIGINT para shutdown graceful en contenedores
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(signum, frame):  # noqa: ANN001
        logger.info("Worker: signal recibido, iniciando shutdown graceful...")
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Worker listo. Esperando jobs... (cola no implementada — ADR-003)")

    # Loop no-op: espera hasta recibir signal de shutdown
    while not stop_event.is_set():
        await asyncio.sleep(5)
        logger.debug("Worker heartbeat (no-op)")

    logger.info("Worker detenido.")


if __name__ == "__main__":
    asyncio.run(main())
