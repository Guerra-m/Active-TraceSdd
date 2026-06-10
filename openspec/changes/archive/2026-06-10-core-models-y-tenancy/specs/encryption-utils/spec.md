## ADDED Requirements

### Requirement: AES-256-GCM encryption utility for PII attributes
The system SHALL provide `core/encryption.py` with two public functions: `encrypt(plaintext: str) -> str` and `decrypt(ciphertext: str) -> str`. The cipher SHALL be AES-256-GCM. The encryption key SHALL be derived from `Settings.ENCRYPTION_KEY` (32 bytes / 256 bits). Each `encrypt()` call SHALL generate a fresh 12-byte random nonce. The serialized output SHALL be a single Base64 string encoding `nonce || ciphertext || tag` (or equivalent self-contained format).

#### Scenario: Encrypt and decrypt round-trip
- **WHEN** a plaintext string is encrypted with `encrypt()` and then decrypted with `decrypt()`
- **THEN** the result SHALL equal the original plaintext

#### Scenario: Different ciphertexts for same plaintext (nonce randomness)
- **WHEN** the same plaintext is encrypted twice
- **THEN** the two ciphertexts SHALL be different (due to random nonce)

#### Scenario: Tampered ciphertext fails decryption
- **WHEN** a ciphertext is modified before calling `decrypt()`
- **THEN** `decrypt()` SHALL raise an `InvalidToken` or equivalent integrity error

### Requirement: PII never appears in logs or exceptions
The system SHALL ensure that plaintext values of encrypted attributes (DNI, CUIL, CBU, email PII) are never written to application logs, error messages, or exception traces. The encryption/decryption layer SHALL be the only place that handles plaintext PII.

#### Scenario: Encryption error does not leak plaintext
- **WHEN** `encrypt()` raises an exception (e.g., invalid key length)
- **THEN** the exception message SHALL NOT contain the plaintext value passed to `encrypt()`

### Requirement: ENCRYPTION_KEY validation at startup
The system SHALL validate at application startup that `ENCRYPTION_KEY` is exactly 32 bytes (256 bits). If the key is missing, shorter, or longer, the application SHALL fail to start with a clear error message.

#### Scenario: Invalid key length prevents startup
- **WHEN** `Settings` is initialized with an `ENCRYPTION_KEY` that is not 32 bytes
- **THEN** a `ValidationError` (Pydantic) SHALL be raised before any request is served

#### Scenario: Valid 32-byte key allows startup
- **WHEN** `Settings` is initialized with a valid 32-byte `ENCRYPTION_KEY`
- **THEN** the application SHALL start successfully and `encrypt()`/`decrypt()` SHALL be available
