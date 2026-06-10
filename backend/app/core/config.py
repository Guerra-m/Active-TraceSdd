"""Configuracion tipada de la aplicacion.

Carga las variables de entorno desde un archivo .env (y el entorno del proceso)
mediante pydantic-settings. La validacion ocurre en el arranque: si falta una
variable requerida o un valor no satisface su tipo/longitud, la instanciacion
falla con un error explicito y la app no arranca.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion central de active-trace backend.

    Todas las variables son requeridas salvo las que tienen default.
    Las claves de seguridad se validan en longitud minima.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Base de datos ----
    database_url: str = Field(
        ...,
        description="URL async de PostgreSQL (postgresql+asyncpg://...)",
    )
    database_url_test: str | None = Field(
        default=None,
        description="URL de la base de datos de test (opcional, para CI/test local)",
    )

    # ---- Seguridad ----
    secret_key: str = Field(
        ...,
        min_length=32,
        description="Clave de firma JWT. Minimo 32 caracteres.",
    )
    encryption_key: str = Field(
        ...,
        description=(
            "Clave AES-256 para cifrado en reposo (app/core/encryption.py). "
            "Debe tener EXACTAMENTE 32 caracteres ASCII. "
            "Ejemplo: ENCRYPTION_KEY=12345678901234567890123456789012 "
            "No usar Base64 ni hex — pasar los 32 caracteres directamente."
        ),
    )

    # ---- Tokens ----
    access_token_expire_minutes: int = Field(
        default=15,
        gt=0,
        description="Tiempo de vida del access token JWT en minutos.",
    )
    refresh_token_expire_days: int = Field(
        default=30,
        gt=0,
        description="Tiempo de vida del refresh token en días.",
    )

    # ---- Entorno ----
    app_env: str = Field(
        default="development",
        description="Entorno de ejecucion: development | test | production",
    )

    # ---- OpenTelemetry (opcional) ----
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        description="Endpoint OTLP para exportar trazas. Omitir para deshabilitar.",
    )

    @field_validator("secret_key")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY debe tener al menos 32 caracteres (tiene {len(v)})"
            )
        return v

    @field_validator("encryption_key")
    @classmethod
    def encryption_key_exact_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY debe tener exactamente 32 caracteres (tiene {len(v)})"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada).

    Usar esta funcion en lugar de instanciar Settings() directamente permite
    invalidar el cache en tests via get_settings.cache_clear().
    """
    return Settings()
