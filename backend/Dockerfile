# =============================================================================
# active-trace backend — Dockerfile multi-stage
# Convencion Easypanel: variables por entorno, sin secretos hardcodeados.
#
# Etapas:
#   builder  — instala dependencias con uv sobre Python 3.13
#   runtime  — imagen slim, solo entorno + codigo de app/; arranca uvicorn
#
# Build:
#   docker build -t active-trace-api .
# Run:
#   docker run --env-file .env -p 8000:8000 active-trace-api
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — instala dependencias
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Instalar uv (gestor de dependencias rapido con lockfile determinista)
RUN pip install --no-cache-dir uv==0.7.13

WORKDIR /build

# Copiar solo pyproject.toml primero para aprovechar cache de capas Docker
COPY pyproject.toml ./

# Instalar dependencias en un venv aislado (sin dev deps)
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
        --no-cache \
        -e "." \
        fastapi uvicorn[standard] sqlalchemy[asyncio] alembic asyncpg \
        pydantic pydantic-settings argon2-cffi "python-jose[cryptography]" \
        cryptography pyotp \
        "opentelemetry-sdk" opentelemetry-instrumentation-fastapi \
        "opentelemetry-exporter-otlp" python-json-logger \
        python-multipart openpyxl httpx "pydantic[email]"

# ---------------------------------------------------------------------------
# Stage 2: runtime — imagen minima sin toolchain de build
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# Metadatos de imagen
LABEL maintainer="active-trace team" \
      version="0.1.0" \
      description="active-trace backend — FastAPI async sobre PostgreSQL"

# Crear usuario sin privilegios para seguridad en contenedor
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copiar entorno virtual del builder (sin toolchain)
COPY --from=builder /opt/venv /opt/venv

# Copiar codigo de la aplicacion
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Asegurar permisos
RUN chown -R appuser:appgroup /app

# Variables de entorno de runtime
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Puerto de la API (configurable via EXPOSE; bind real en CMD)
EXPOSE 8000

# Cambiar a usuario sin privilegios
USER appuser

# Healthcheck nativo del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Entrypoint: uvicorn apuntando al factory ASGI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--no-access-log"]
