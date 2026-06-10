"""Logging estructurado en JSON para active-trace.

Configura el logger raiz para emitir una linea JSON por evento con los campos
minimos: timestamp (ISO-8601), level y message.

Uso:
    from app.core.logging import setup_logging
    setup_logging()  # llamar una vez en el arranque (lifespan de main.py)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("mensaje", extra={"campo": "valor"})

Reglas de seguridad:
    - NUNCA loguear secretos (SECRET_KEY, ENCRYPTION_KEY, passwords, tokens).
    - NUNCA loguear PII en texto plano (CBU, DNI, datos personales).
    - Los handlers de terceros (uvicorn, sqlalchemy) se configuran al mismo nivel.
"""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter

_CONFIGURED = False

_JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configura el logger raiz con formato JSON estructurado.

    Idempotente: si ya fue configurado, no hace nada. Llamar en el arranque
    del lifespan de la app FastAPI.

    Args:
        level: Nivel de log como string ("DEBUG", "INFO", "WARNING", "ERROR").
               Por defecto "INFO".
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Formatter JSON: una linea por evento
    formatter = JsonFormatter(
        fmt=_JSON_FORMAT,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )

    # Handler a stdout (agregadores de logs leen stdout en contenedores)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers previos para evitar duplicados en recargas
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silenciar loggers ruidosos de terceros a nivel WARNING
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre dado.

    Wrapper de conveniencia para obtener loggers del modulo.

    Args:
        name: Nombre del logger, tipicamente __name__ del modulo.
    """
    return logging.getLogger(name)


def reset_logging() -> None:
    """Resetea el estado de configuracion (util en tests)."""
    global _CONFIGURED
    _CONFIGURED = False
