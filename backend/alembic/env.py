"""Alembic env.py — engine sync (psycopg2) para migraciones.

Alembic se conecta con psycopg2 (sync). El runtime de la app usa asyncpg,
pero Alembic no necesita async y psycopg2 evita problemas de event loop
en Windows con Python 3.12+.

Uso:
    alembic upgrade head          # aplica migraciones pendientes
    alembic revision --autogenerate -m "descripcion"  # genera nueva migracion
    alembic downgrade -1          # revierte ultima migracion

Convencion del proyecto:
    - Una migracion Alembic por cambio de schema (regla dura #15)
    - La migracion 001 es de C-02 (core-models-y-tenancy)
    - Soft delete: nunca DROP de columnas con datos de negocio
"""

import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Configuracion de Alembic
# ---------------------------------------------------------------------------

# Cargar .env desde el directorio del backend (un nivel arriba de alembic/)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Construir URL sync: reemplaza +asyncpg por +psycopg2 para migraciones
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    _sync_url = _db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    alembic_config.set_main_option("sqlalchemy.url", _sync_url)

import app.models  # noqa: F401 — registra todos los modelos en Base.metadata
from app.core.database import Base

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Modo offline
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Modo online (sync)
# ---------------------------------------------------------------------------


def run_migrations_online() -> None:
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
