"""Bootstrap de la aplicacion FastAPI — active-trace backend.

Responsabilidades de este modulo:
  1. Definir el lifespan (startup / shutdown) del engine async.
  2. Inicializar logging estructurado JSON y OpenTelemetry.
  3. Registrar middleware y routers.
  4. Exponer la factory create_app() para tests y el entrypoint ASGI.

NO contiene logica de negocio. Sigue el flujo unidireccional:
  Routers → Services → Repositories → Models (regla #11).
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_engine, init_engine
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan de la app FastAPI: startup → yield → shutdown.

    Startup:
      - Inicializar logging JSON
      - Inicializar engine async de SQLAlchemy
      - Inicializar OpenTelemetry (no-op si no hay endpoint OTLP)

    Shutdown:
      - Cerrar el engine y liberar conexiones del pool
    """
    # 1. Logging debe inicializarse primero
    settings = get_settings()
    setup_logging(level="DEBUG" if settings.app_env == "development" else "INFO")

    logger.info("active-trace backend arrancando", extra={"env": settings.app_env})

    # 2. Engine de base de datos
    init_engine()
    logger.info("Engine async de DB inicializado.")

    # 3. OpenTelemetry (graceful: no bloquea el arranque)
    from app.core.observability import setup_telemetry
    setup_telemetry(app)

    # 4. Worker de comunicaciones (asyncio background task)
    from app.core.database import async_session_factory
    from app.integrations.email_sender import get_sender
    from app.workers.comunicacion_worker import ComunicacionWorker
    from contextlib import asynccontextmanager as _acm

    def _make_db():
        return async_session_factory()

    _worker = ComunicacionWorker(
        db_factory=_make_db,
        sender=get_sender(),
        poll_interval_s=settings.worker_poll_interval_s,
    )
    _worker_task = asyncio.create_task(_worker.loop())

    yield  # La app esta lista para recibir requests

    # Shutdown
    logger.info("active-trace backend apagandose...")
    _worker.stop()
    _worker_task.cancel()
    await close_engine()
    logger.info("Engine async de DB cerrado.")


def create_app() -> FastAPI:
    """Factory que crea y configura la instancia de FastAPI.

    Usar esta funcion en tests y en el entrypoint ASGI.
    """
    settings = get_settings()

    application = FastAPI(
        title="active-trace",
        description="Plataforma de gestion academica y trazabilidad multi-tenant sobre Moodle.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    # ---- Middleware ----
    # CORS: abierto en desarrollo, configurar dominios en produccion
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env != "production" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Routers ----
    from app.api.v1.routers.health import router as health_router
    application.include_router(health_router)

    from app.api.v1.routers.auth import router as auth_router
    application.include_router(auth_router)

    from app.api.v1.routers.rbac import router as rbac_router
    application.include_router(rbac_router)

    from app.api.v1.routers.impersonation import router as impersonation_router
    application.include_router(impersonation_router)

    from app.api.v1.routers.estructura import router as estructura_router
    application.include_router(estructura_router)

    from app.api.v1.routers.usuarios import router as usuarios_router
    application.include_router(usuarios_router)

    from app.api.v1.routers.asignaciones import router as asignaciones_router
    application.include_router(asignaciones_router)

    from app.api.v1.routers.padron import router as padron_router
    application.include_router(padron_router)

    from app.api.v1.routers.calificaciones import router as calificaciones_router
    application.include_router(calificaciones_router)

    from app.api.v1.routers.analisis import router as analisis_router
    application.include_router(analisis_router)

    from app.api.v1.routers.comunicaciones import router as comunicaciones_router
    application.include_router(comunicaciones_router)

    from app.api.v1.routers.equipos import router as equipos_router
    application.include_router(equipos_router)

    from app.api.v1.routers.encuentros import router as encuentros_router
    application.include_router(encuentros_router)

    from app.api.v1.routers.guardias import router as guardias_router
    application.include_router(guardias_router)

    from app.api.v1.routers.coloquios import router as coloquios_router
    application.include_router(coloquios_router)

    from app.api.v1.routers.avisos import router as avisos_router
    application.include_router(avisos_router)

    from app.api.v1.routers.tareas import router as tareas_router
    application.include_router(tareas_router)

    from app.api.v1.routers.programas import programas_router, fechas_router
    application.include_router(programas_router)
    application.include_router(fechas_router)

    from app.api.v1.routers.perfil import router as perfil_router
    application.include_router(perfil_router)

    from app.api.v1.routers.auditoria import router as auditoria_router
    application.include_router(auditoria_router)

    return application


# Entrypoint ASGI para uvicorn:
#   uvicorn app.main:app --host 0.0.0.0 --port 8000
app = create_app()
