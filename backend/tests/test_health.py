"""Tests para GET /health — liveness + readiness de DB.

TDD cycle:
  5.1 RED    — este archivo (tests escritos antes que el router)
  5.2 GREEN  — implementar api/v1/routers/health.py
  5.3 TRIANG — caso DB down: reporta database:down sin caerse el proceso
"""

import pytest


class TestHealthLiveness:
    """Scenario: La aplicacion esta viva."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, async_client):
        """GET /health responde 200 OK."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_is_json(self, async_client):
        """GET /health devuelve Content-Type application/json."""
        response = await async_client.get("/health")
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_health_has_status_field(self, async_client):
        """GET /health incluye un campo 'status' en el cuerpo JSON."""
        response = await async_client.get("/health")
        body = response.json()
        assert "status" in body

    @pytest.mark.asyncio
    async def test_health_status_is_ok(self, async_client):
        """GET /health reporta status='ok' cuando la app esta funcionando."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["status"] == "ok"


class TestHealthDatabaseReadiness:
    """Scenario: Readiness de la base de datos en el health-check."""

    @pytest.mark.asyncio
    async def test_health_has_database_field(self, async_client):
        """GET /health incluye un campo 'database' en el cuerpo JSON."""
        response = await async_client.get("/health")
        body = response.json()
        assert "database" in body

    @pytest.mark.asyncio
    async def test_health_database_up_when_db_reachable(self, async_client):
        """GET /health reporta database='up' cuando la DB responde."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["database"] == "up"


class TestHealthDatabaseDown:
    """Scenario: Base de datos inalcanzable — no tira el proceso."""

    @pytest.mark.asyncio
    async def test_health_database_down_when_db_unreachable(self, db_engine):
        """GET /health reporta database='down' cuando la DB falla, sin caerse."""
        from unittest.mock import AsyncMock, patch

        from app.main import create_app
        from httpx import ASGITransport, AsyncClient

        # Crear una app nueva para este test
        app = create_app()

        # Parchear get_db para que simule un error de conexion
        async def broken_get_db():
            raise ConnectionError("DB unreachable (simulado en test)")
            yield  # make it a generator

        with patch("app.api.v1.routers.health.get_db", broken_get_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.get("/health")

        # El proceso no se cae — sigue respondiendo con 200
        assert response.status_code == 200
        body = response.json()
        assert body["database"] == "down"
