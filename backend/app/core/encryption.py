"""Utilidad de cifrado AES-256-GCM para atributos PII en reposo.

Expone dos funciones publicas:
  - encrypt(plaintext: str) -> str
  - decrypt(ciphertext: str) -> str

Formato de serializacion:
  nonce_b64:ciphertext_b64
  donde ciphertext_b64 contiene tag (16 bytes) + datos cifrados, tal como
  los produce AESGCM de la libreria cryptography.

Decision D3 del design:
  - AES-256-GCM (AEAD): confidencialidad + autenticidad en una sola primitiva.
  - Nonce de 12 bytes random por cada llamada a encrypt() — nunca reutilizar.
  - Clave de 32 bytes derivada de Settings.ENCRYPTION_KEY.
  - Resultado almacenable en columna TEXT de PostgreSQL.

REGLA CRITICA: NUNCA loggear el plaintext ni el ciphertext. Las excepciones
no deben contener el valor sensible en su mensaje. Esta restriccion es
permanente y no se puede relajar.
"""

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    """Obtiene la clave de cifrado desde Settings y la convierte a bytes.

    La clave se lee en cada operacion para soportar rotacion sin reinicio.
    Se valida que tenga exactamente 32 bytes (AES-256).

    Raises:
        ValueError: Si la clave tiene longitud incorrecta (nunca deberia ocurrir
            si Settings esta bien configurada, pero es un fail-safe).
    """
    from app.core.config import get_settings

    key_str = get_settings().encryption_key
    key_bytes = key_str.encode("utf-8")

    if len(key_bytes) != 32:
        # No incluir la clave en el mensaje de error
        raise ValueError(
            f"ENCRYPTION_KEY debe tener exactamente 32 bytes; tiene {len(key_bytes)}"
        )

    return key_bytes


def encrypt(plaintext: str) -> str:
    """Cifra un string con AES-256-GCM y retorna el resultado serializado.

    Args:
        plaintext: Texto a cifrar (puede ser vacio).

    Returns:
        String en formato ``nonce_b64:ciphertext_b64`` donde ciphertext_b64
        contiene los 16 bytes de tag GCM seguidos del texto cifrado.

    Note:
        Cada llamada genera un nonce random de 12 bytes. Por eso dos llamadas
        con el mismo plaintext producen ciphertexts distintos — es el
        comportamiento correcto y esperado.
    """
    key = _get_key()
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)
    plaintext_bytes = plaintext.encode("utf-8")

    # AESGCM.encrypt() retorna tag (16 bytes) + ciphertext concatenados
    encrypted = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)

    nonce_b64 = base64.b64encode(nonce).decode("ascii")
    encrypted_b64 = base64.b64encode(encrypted).decode("ascii")

    return f"{nonce_b64}:{encrypted_b64}"


def decrypt(ciphertext: str) -> str:
    """Descifra un string cifrado con encrypt() y retorna el plaintext.

    Args:
        ciphertext: String serializado en formato ``nonce_b64:encrypted_b64``.

    Returns:
        El plaintext original.

    Raises:
        InvalidTag: Si el ciphertext fue alterado (fallo de autenticidad GCM).
        ValueError: Si el formato del ciphertext es invalido.

    Note:
        InvalidTag es la excepcion correcta cuando el ciphertext fue modificado
        o la clave es incorrecta — no se incluye el plaintext en el error.
    """
    try:
        parts = ciphertext.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Formato de ciphertext invalido: se esperaba 'nonce_b64:data_b64'")

        nonce = base64.b64decode(parts[0])
        encrypted = base64.b64decode(parts[1])
    except Exception as exc:
        # Re-levantar como ValueError sin incluir datos sensibles
        raise ValueError("Ciphertext malformado o no decodificable como Base64") from exc

    key = _get_key()
    aesgcm = AESGCM(key)

    # decrypt() lanza InvalidTag si la autenticidad falla (tampered o clave incorrecta)
    plaintext_bytes = aesgcm.decrypt(nonce, encrypted, associated_data=None)
    return plaintext_bytes.decode("utf-8")
