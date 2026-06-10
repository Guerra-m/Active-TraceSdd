"""Fixtures compartidas para la suite de tests de active-trace backend.

Convencion de base de datos:
  - Los tests que requieren DB usan la variable DATABASE_URL_TEST del entorno.
  - Si no esta definida, se usa el servicio postgres del docker-compose (mismo
    host/port que la app, base de datos 'trace_test').
  - NUNCA se mockea la base de datos: los tests validan conexion real (regla #4).
  - Cada test recibe una sesion con rollback al final para aislamiento.

Fixtures disponibles:
  - settings       : instancia de Settings con env de test
  - db_engine      : AsyncEngine apuntando a la DB de test (scope=session)
  - db_session     : AsyncSession por test (rollback al terminar)
  - async_client   : httpx.AsyncClient para tests de la API REST
  - app            : instancia FastAPI para tests de arranque
  - test_tenant    : Tenant de prueba persistido (scope=function)
  - test_tenant_b  : Segundo Tenant para tests de aislamiento multi-tenant
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

# URL de DB de test: DATABASE_URL_TEST del entorno, o fallback a trace_test local
_DEFAULT_TEST_DB = "postgresql+asyncpg://trace:trace@127.0.0.1:5432/trace_test"
TEST_DATABASE_URL = os.environ.get("DATABASE_URL_TEST", _DEFAULT_TEST_DB)

# En Windows, asyncpg falla contra Docker con "localhost" (resuelve a ::1/IPv6).
# Normalizamos a 127.0.0.1 para forzar IPv4.
if sys.platform == "win32":
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("@localhost:", "@127.0.0.1:")



# Inyectar en el entorno para que Settings la lea si se usa en el contexto de test
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("DATABASE_URL_TEST", TEST_DATABASE_URL)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")
os.environ.setdefault("ENCRYPTION_KEY", "test-encrypt-key-32characters!!!")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("APP_ENV", "test")


# ---------------------------------------------------------------------------
# Engine de test (scope session — un solo engine para toda la suite)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Engine async apuntando a la base de datos de test.

    Se inicializa una vez por session de pytest y se cierra al final.
    Tambien inicializa el engine global de app.core.database para que
    las dependencies (get_db) funcionen en los tests de la API.

    Crea todas las tablas desde Base.metadata al inicio y las elimina al final.
    Esto garantiza que los modelos de C-02 (Tenant, tablas de dominio) existan.
    """
    from app.core import database as db_module
    from app.core.database import Base
    import app.models  # noqa: F401 — registrar todos los modelos en Base.metadata

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Crear tablas desde metadata (alternativa a alembic en tests)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Inicializar el modulo de database apuntando a la DB de test
    db_module._engine = engine
    db_module.async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    yield engine

    # Limpiar tablas al final de la session de tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    db_module._engine = None
    db_module.async_session_factory = None


# ---------------------------------------------------------------------------
# Sesion de test (scope function — rollback por test para aislamiento)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Sesion async por test con rollback al terminar.

    Garantiza aislamiento entre tests sin necesidad de truncar tablas.
    """
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# ---------------------------------------------------------------------------
# Fixtures de Tenant para tests de dominio y aislamiento multi-tenant
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession):
    """Tenant de prueba principal persistido en la DB de test.

    Usado como tenant propietario en tests de modelos de dominio y repositories.
    Slug: 'test-tenant'
    """
    from app.models.tenant import Tenant

    tenant = Tenant(name="Test Institution", slug="test-tenant")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_tenant_b(db_session: AsyncSession):
    """Segundo Tenant para tests de aislamiento multi-tenant.

    Se usa en tests que verifican que un tenant NO puede ver datos del otro.
    Slug: 'test-tenant-b'
    """
    from app.models.tenant import Tenant

    tenant = Tenant(name="Test Institution B", slug="test-tenant-b")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.refresh(tenant)
    return tenant


# ---------------------------------------------------------------------------
# Aislamiento entre tests: truncar tablas después de cada test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(db_engine: AsyncEngine):
    """Trunca todas las tablas al final de cada test para aislamiento.

    Los fixtures de usuario hacen commit() explícito (necesario para que el
    endpoint FastAPI los vea via su propia sesión). Este fixture garantiza
    que esos datos no contaminen el siguiente test.
    """
    from sqlalchemy import text
    import app.models  # noqa: F401 — asegura que todos los modelos estén registrados
    from app.core.database import Base

    yield  # el test corre aquí

    # Limpiar estado in-memory del rate limiter para aislamiento entre tests
    from app.services.auth_service import _rate_limit_store
    _rate_limit_store.clear()

    table_names = [t.name for t in reversed(Base.metadata.sorted_tables)]
    async with db_engine.begin() as conn:
        for tname in table_names:
            await conn.execute(text(f'TRUNCATE TABLE "{tname}" RESTART IDENTITY CASCADE'))


# ---------------------------------------------------------------------------
# App FastAPI y cliente HTTP async
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app(db_engine: AsyncEngine):
    """Instancia de la app FastAPI configurada para tests.

    Usa el engine de test ya inicializado en db_engine.
    """
    from app.main import create_app

    application = create_app()
    return application


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """httpx.AsyncClient configurado para llamar a la app FastAPI en tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
