"""Tests para la utilidad de cifrado AES-256-GCM.

TDD cycle:
  - 2.2 RED  : round-trip, nonces distintos, tampered ciphertext
  - 2.4 TRIANGULATE : ENCRYPTION_KEY invalida, ciphertext truncado
"""

import base64
import os

import pytest
from cryptography.exceptions import InvalidTag
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers de test
# ---------------------------------------------------------------------------


def _valid_key_32() -> str:
    """Genera una clave válida de exactamente 32 bytes ASCII."""
    return "A" * 32


def _valid_key_env(monkeypatch) -> None:
    """Inyecta una ENCRYPTION_KEY válida en el entorno para Settings."""
    monkeypatch.setenv("ENCRYPTION_KEY", _valid_key_32())


# ---------------------------------------------------------------------------
# 2.2 RED — Round-trip, nonce distinto, tampered ciphertext
# ---------------------------------------------------------------------------


class TestEncryptDecryptRoundTrip:
    """Tests básicos del ciclo encrypt → decrypt."""

    def test_round_trip_simple_string(self):
        """encrypt luego decrypt debe devolver el texto original."""
        from app.core.encryption import decrypt, encrypt

        plaintext = "hola mundo"
        ciphertext = encrypt(plaintext)
        assert decrypt(ciphertext) == plaintext

    def test_round_trip_unicode_string(self):
        """encrypt/decrypt debe funcionar con caracteres unicode."""
        from app.core.encryption import decrypt, encrypt

        plaintext = "nombre: José María Ñoño — DNI: 12.345.678"
        assert decrypt(encrypt(plaintext)) == plaintext

    def test_round_trip_empty_string(self):
        """encrypt/decrypt debe funcionar con string vacío."""
        from app.core.encryption import decrypt, encrypt

        assert decrypt(encrypt("")) == ""

    def test_different_nonces_same_plaintext(self):
        """Dos cifrados del mismo texto deben producir ciphertexts distintos."""
        from app.core.encryption import encrypt

        ct1 = encrypt("mismo texto")
        ct2 = encrypt("mismo texto")
        assert ct1 != ct2, "El nonce random debe generar ciphertexts distintos"

    def test_ciphertext_format_has_two_parts(self):
        """El ciphertext debe tener el formato nonce_b64:rest_b64."""
        from app.core.encryption import encrypt

        ct = encrypt("test")
        parts = ct.split(":")
        assert len(parts) == 2, f"Formato incorrecto: {ct!r}"

        # Verificar que ambas partes son Base64 válido
        for part in parts:
            base64.b64decode(part)  # no debe levantar

    def test_nonce_is_12_bytes(self):
        """El nonce debe ser de 12 bytes (96 bits) según NIST GCM."""
        from app.core.encryption import encrypt

        ct = encrypt("test nonce size")
        nonce_b64 = ct.split(":")[0]
        nonce_bytes = base64.b64decode(nonce_b64)
        assert len(nonce_bytes) == 12


class TestTamperedCiphertextRaisesError:
    """Tests de integridad: ciphertext alterado debe fallar."""

    def test_altered_ciphertext_raises_invalid_tag(self):
        """Modificar el ciphertext (bytes) debe levantar InvalidTag."""
        from app.core.encryption import decrypt, encrypt

        ct = encrypt("dato sensible")
        parts = ct.split(":")
        # Decodificar la segunda parte, alterar un byte interior, re-encodear
        encrypted_bytes = base64.b64decode(parts[1])
        # Alterar el byte 5 (dentro del ciphertext, no el tag)
        altered = bytearray(encrypted_bytes)
        altered[5] ^= 0xFF
        tampered_ct = base64.b64encode(bytes(altered)).decode()
        tampered = parts[0] + ":" + tampered_ct

        with pytest.raises(InvalidTag):
            decrypt(tampered)

    def test_altered_nonce_raises_invalid_tag(self):
        """Modificar el nonce debe levantar InvalidTag."""
        from app.core.encryption import decrypt, encrypt

        ct = encrypt("otro dato")
        parts = ct.split(":")
        # Alterar el nonce bit a bit
        nonce_bytes = base64.b64decode(parts[0])
        altered_nonce = bytes([b ^ 0xFF for b in nonce_bytes])
        tampered = base64.b64encode(altered_nonce).decode() + ":" + parts[1]

        with pytest.raises(InvalidTag):
            decrypt(tampered)

    def test_truncated_ciphertext_raises_error(self):
        """Un ciphertext truncado debe levantar una excepción."""
        from app.core.encryption import decrypt, encrypt

        ct = encrypt("truncar esto")
        # Truncar a solo los primeros 5 chars (claramente inválido)
        truncated = ct[:5]

        with pytest.raises(Exception):  # InvalidTag o ValueError
            decrypt(truncated)


# ---------------------------------------------------------------------------
# 2.4 TRIANGULATE — ENCRYPTION_KEY inválida, ciphertext truncado
# ---------------------------------------------------------------------------


class TestEncryptionKeyValidation:
    """Tests de validación de ENCRYPTION_KEY en Settings."""

    def test_settings_rejects_key_shorter_than_32_bytes(self, monkeypatch):
        """Settings debe levantar ValidationError si ENCRYPTION_KEY < 32 bytes."""
        # Limpiar el cache de settings para forzar re-inicializacion
        from app.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("ENCRYPTION_KEY", "clave-corta")

        with pytest.raises(ValidationError):
            from app.core.config import Settings

            Settings()

        get_settings.cache_clear()

    def test_settings_rejects_key_longer_than_32_bytes(self, monkeypatch):
        """Settings debe levantar ValidationError si ENCRYPTION_KEY > 32 bytes."""
        from app.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("ENCRYPTION_KEY", "clave-demasiado-larga-para-aes-256-gcm!!")

        with pytest.raises(ValidationError):
            from app.core.config import Settings

            Settings()

        get_settings.cache_clear()

    def test_settings_accepts_valid_32_byte_key(self, monkeypatch):
        """Settings debe aceptar una ENCRYPTION_KEY de exactamente 32 bytes."""
        from app.core.config import get_settings, Settings

        get_settings.cache_clear()
        monkeypatch.setenv("ENCRYPTION_KEY", "A" * 32)
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://trace:trace@localhost:5432/trace")

        settings = Settings()
        assert len(settings.encryption_key) == 32

        get_settings.cache_clear()

    def test_encryption_error_does_not_leak_plaintext(self):
        """Las excepciones de cifrado NO deben contener el plaintext en el mensaje."""
        from app.core.encryption import decrypt

        sensitive_value = "DNI:12345678-SECRETO"
        malformed_ct = "invalido:nada"

        try:
            decrypt(malformed_ct)
        except Exception as exc:
            # El plaintext sensible no debe aparecer en el error
            assert sensitive_value not in str(exc)
