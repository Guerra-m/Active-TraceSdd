"""Bootstrap de la aplicacion FastAPI — active-trace backend.

Responsabilidades de este modulo:
  1. Definir el lifespan (startup / shutdown) del engine async.
  2. Inicializar logging estructurado JSON y OpenTelemetry.
  3. Registrar middleware y routers.
  4. Exponer la factory create_app() para tests y el entrypoint ASGI.

NO contiene logica de negocio. Sigue el flujo unidireccional:
  Routers → Services → Repositories → Models (regla #11).
"""

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

    yield  # La app esta lista para recibir requests

    # Shutdown
    logger.info("active-trace backend apagandose...")
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

    return application


# Entrypoint ASGI para uvicorn:
#   uvicorn app.main:app --host 0.0.0.0 --port 8000
app = create_app()
