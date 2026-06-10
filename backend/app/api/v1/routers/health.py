"""Router de health-check — GET /health.

Reporta:
  - status: "ok" cuando la app esta en funcionamiento (liveness)
  - database: "up" | "down" segun si la DB responde a SELECT 1 (readiness)

El endpoint captura errores de conexion a la DB y reporta degradacion sin
caerse el proceso (fail-graceful). Ver spec: health-check/spec.md D4.
"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check — liveness + readiness de DB")
async def health_check():
    """Verifica que la app esta viva y que la DB es alcanzable.

    Returns:
        200 OK con JSON::

            {"status": "ok", "database": "up"}

        Si la DB esta caida, responde igualmente 200 (no crashea)::

            {"status": "ok", "database": "down"}
    """
    db_status = "down"

    try:
        # Obtener una sesion de la dependency y ejecutar SELECT 1
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                db_status = "up"
            break  # solo necesitamos una iteracion
    except Exception as exc:
        logger.warning("health_check: DB no alcanzable", extra={"error": str(exc)})
        db_status = "down"

    return JSONResponse(
        status_code=200,
        content={"status": "ok", "database": db_status},
    )
