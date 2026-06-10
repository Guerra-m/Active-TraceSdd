"""Tests para el arranque de la app FastAPI — lifespan correcto.

TDD cycle:
  5.4 RED    — este archivo (tests escritos antes que main.py)
  5.5 GREEN  — implementar app/main.py con lifespan, middleware y router
"""

import pytest


class TestAppStartup:
    """Scenario: La app FastAPI se instancia y arranca sin error."""

    def test_create_app_returns_fastapi_instance(self, db_engine):
        """create_app() devuelve una instancia de FastAPI."""
        from fastapi import FastAPI
        from app.main import create_app

        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_has_health_route(self, db_engine):
        """La app registra la ruta GET /health."""
        from app.main import create_app

        app = create_app()
        routes = {route.path for route in app.routes}
        assert "/health" in routes

    @pytest.mark.asyncio
    async def test_app_lifespan_does_not_crash(self, db_engine):
        """El lifespan de la app arranca y cierra sin lanzar excepcion."""
        from app.main import create_app
        from httpx import ASGITransport, AsyncClient

        app = create_app()

        # Levantar la app con lifespan completo via ASGI
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_app_returns_404_for_unknown_routes(self, db_engine):
        """Rutas no registradas devuelven 404 (no 500)."""
        from app.main import create_app
        from httpx import ASGITransport, AsyncClient

        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/ruta-que-no-existe")
            assert response.status_code == 404
