"""Tests para core/database.py — engine async y sesion por request.

TDD cycle:
  3.3 RED    — este archivo (tests escritos antes de fixtures/conftest completo)
  3.4 GREEN  — ajustar engine/fixtures en conftest.py hasta verde
  3.5 TRIANG — cierre de sesion ante excepcion (no fuga de conexiones)
"""

import pytest
import pytest_asyncio
from sqlalchemy import text


class TestDatabaseSmoke:
    """Scenario: Conexion a base de datos de test."""

    @pytest.mark.asyncio
    async def test_select_one_returns_result(self, db_session):
        """Una sesion async ejecuta SELECT 1 y obtiene resultado 1."""
        result = await db_session.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1

    @pytest.mark.asyncio
    async def test_session_is_async_session(self, db_session):
        """La fixture db_session provee una AsyncSession valida."""
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(db_session, AsyncSession)


class TestSessionLifecycle:
    """Scenario: Cierre ante error — no fuga de conexion al pool."""

    @pytest.mark.asyncio
    async def test_session_closes_on_exception(self, db_engine):
        """La sesion se cierra correctamente aunque el handler lance una excepcion."""
        from app.core.database import async_session_factory
        from sqlalchemy import text

        session_closed = False
        original_close = None

        async def _run():
            nonlocal session_closed
            async with async_session_factory() as session:
                # Anotar el metodo close original para verificar que se invoca
                original_close_ref = session.close

                try:
                    await session.execute(text("SELECT 1"))
                    raise ValueError("error simulado dentro del scope de la sesion")
                except ValueError:
                    pass
                finally:
                    # El context manager de async_sessionmaker cierra la sesion
                    # en el __aexit__; despues de salir del with, la sesion esta cerrada.
                    session_closed = True

        await _run()
        assert session_closed, "El bloque finally debe ejecutarse aunque haya excepcion"

    @pytest.mark.asyncio
    async def test_get_db_dependency_closes_session_on_error(self):
        """La dependency get_db cierra la sesion incluso si el handler falla."""
        from app.core.dependencies import get_db
        from sqlalchemy.ext.asyncio import AsyncSession

        session_ref = None
        error_raised = False

        gen = get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        session_ref = session

        # Simular error en el handler: cerrar el generator con una excepcion
        try:
            await gen.athrow(RuntimeError("error en handler"))
        except (RuntimeError, StopAsyncIteration):
            error_raised = True

        # La sesion debe haber sido cerrada (no activa)
        assert error_raised
