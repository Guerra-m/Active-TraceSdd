"""Conexion async a PostgreSQL con SQLAlchemy 2.0.

Expone:
  - engine: AsyncEngine (creado lazy, inicializado en lifespan)
  - async_session_factory: async_sessionmaker para abrir sesiones por request
  - Base: clase declarativa para todos los modelos ORM del proyecto

Patron de uso:
  - El engine se inicializa una vez en el lifespan de la app (app/main.py).
  - Las sesiones se obtienen a traves de la dependency get_db() (core/dependencies.py).
  - Nunca crear sesiones directamente fuera de get_db() o fixtures de test.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Base declarativa — todos los modelos ORM heredan de esta clase
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM de active-trace."""


# ---------------------------------------------------------------------------
# Engine y session factory — inicializados en lifespan (ver app/main.py)
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str | None = None) -> AsyncEngine:
    """Crea e inicializa el engine async.

    Llamar una sola vez en el lifespan de la app o en fixtures de test.
    Si database_url es None, se usa el valor de Settings.
    """
    global _engine, async_session_factory

    url = database_url or get_settings().database_url
    _engine = create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return _engine


def get_engine() -> AsyncEngine:
    """Devuelve el engine inicializado.

    Raises RuntimeError si init_engine() no fue llamado antes.
    """
    if _engine is None:
        raise RuntimeError(
            "El engine no fue inicializado. "
            "Llamar init_engine() en el lifespan de la app."
        )
    return _engine


async def close_engine() -> None:
    """Cierra el engine y libera todas las conexiones del pool.

    Llamar en el shutdown del lifespan.
    """
    global _engine, async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        async_session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    """Async generator que produce una sesion por request.

    Uso interno; para FastAPI usar la dependency get_db() en core/dependencies.py.
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Session factory no inicializada. "
            "Asegurate de llamar init_engine() antes de get_session()."
        )
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
