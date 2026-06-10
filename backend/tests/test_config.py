"""Tests para core/config.py — Settings (Pydantic v2 / pydantic-settings).

TDD cycle:
  2.1 RED    — este archivo (tests escritos antes que la implementacion)
  2.2 GREEN  — implementar core/config.py
  2.3 TRIANG — casos de variable ausente y tipo invalido
"""

import os
import pytest
from pydantic import ValidationError


class TestSettingsValidLoad:
    """Scenario: Carga valida desde el entorno."""

    def test_settings_instantiates_with_valid_env(self, monkeypatch):
        """Settings se instancia cuando todas las variables requeridas estan presentes."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

        # import deferred para que monkeypatch aplique antes
        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)
        settings = cfg_module.get_settings()

        assert settings.database_url == "postgresql+asyncpg://u:p@localhost:5432/db"
        assert settings.secret_key == "a" * 32
        assert settings.encryption_key == "b" * 32
        assert settings.access_token_expire_minutes == 30

    def test_access_token_default_is_15(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES tiene default 15 cuando no se provee."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)
        settings = cfg_module.get_settings()

        assert settings.access_token_expire_minutes == 15


class TestSettingsInvalidConfig:
    """Scenario: Configuracion invalida o incompleta."""

    def test_missing_required_variable_raises(self, monkeypatch):
        """Falta DATABASE_URL — la instanciacion debe fallar con ValidationError."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)

        with pytest.raises((ValidationError, Exception)):
            # _env_file=None evita leer del .env del entorno de desarrollo
            cfg_module.Settings(_env_file=None)

    def test_secret_key_too_short_raises(self, monkeypatch):
        """SECRET_KEY con menos de 32 caracteres debe fallar la validacion."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)

        with pytest.raises((ValidationError, Exception)):
            cfg_module.Settings()

    def test_encryption_key_wrong_length_raises(self, monkeypatch):
        """ENCRYPTION_KEY con longitud != 32 debe fallar la validacion."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "short")

        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)

        with pytest.raises((ValidationError, Exception)):
            cfg_module.Settings()

    def test_invalid_type_for_integer_field_raises(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES con valor no numerico debe fallar."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-a-number")

        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)

        with pytest.raises((ValidationError, Exception)):
            cfg_module.Settings()
