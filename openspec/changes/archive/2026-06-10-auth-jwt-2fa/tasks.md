# Tasks — auth-jwt-2fa (C-03)

## Task 1 — Modelos ORM
- [x] 1.1 `app/models/user.py` — User con email_encrypted, email_hash, password_hash, totp_secret_encrypted, totp_enabled, is_active + TenantScopedBase
- [x] 1.2 `app/models/refresh_token.py` — RefreshToken con user_id FK, token_hash, expires_at, revoked_at
- [x] 1.3 `app/models/password_reset_token.py` — PasswordResetToken con user_id FK, token_hash, expires_at, used_at
- [x] 1.4 Registrar modelos en `app/models/__init__.py`

## Task 2 — Migración Alembic
- [x] 2.1 `alembic/versions/20260610_002_auth_tables.py` — tablas users, refresh_tokens, password_reset_tokens

## Task 3 — core/security.py
- [x] 3.1 `hash_password(plaintext) -> str` — Argon2id
- [x] 3.2 `verify_password(plaintext, hashed) -> bool`
- [x] 3.3 `hash_email(email: str) -> str` — SHA-256 del email normalizado (lowercase, strip)
- [x] 3.4 `create_access_token(data: dict, expires_delta: timedelta | None) -> str` — JWT HS256
- [x] 3.5 `create_refresh_token() -> tuple[str, str]` — (token_raw, token_hash) usando secrets.token_urlsafe
- [x] 3.6 `verify_token(token: str) -> dict` — verifica firma y expiración, retorna payload
- [x] 3.7 `generate_totp_secret() -> str`
- [x] 3.8 `verify_totp(secret_plaintext: str, code: str) -> bool`

## Task 4 — core/tenancy.py y core/dependencies.py
- [x] 4.1 `get_tenant_id_from_token(payload: dict) -> UUID` — extrae y valida claim tenant_id
- [x] 4.2 `get_current_user(token: str, db: AsyncSession) -> User` en `dependencies.py` — extrae identidad del JWT verificado, NUNCA de parámetros

## Task 5 — Repositories
- [x] 5.1 `app/repositories/user_repository.py` — UserRepository con `find_by_email_hash(email_hash)`, `find_by_id(id)`
- [x] 5.2 `app/repositories/refresh_token_repository.py` — RefreshTokenRepository con `find_by_hash`, `revoke`, `create`
- [x] 5.3 `app/repositories/password_reset_token_repository.py` — CRUD + `find_valid_by_hash`, `mark_used`

## Task 6 — Schemas Pydantic
- [x] 6.1 `app/schemas/auth.py` — todos los schemas request/response con `extra='forbid'`

## Task 7 — AuthService
- [x] 7.1 `app/services/auth_service.py` — `login`, `refresh`, `logout`, `enroll_totp`, `verify_totp_and_issue`, `forgot_password`, `reset_password`
- [x] 7.2 Rate limiting in-memory `_RateLimiter` (5/60s por IP+email_hash)

## Task 8 — Router
- [x] 8.1 `app/api/v1/routers/auth.py` — endpoints: POST /login, /refresh, /logout, /totp/enroll, /totp/verify, /forgot, /reset
- [x] 8.2 Registrar router en `app/api/v1/__init__.py` o `app/main.py`

## Task 9 — config.py
- [x] 9.1 Agregar `refresh_token_expire_days: int = 30` a Settings

## Task 10 — Tests (TDD)
- [x] 10.1 `tests/test_auth.py` — login OK (sin 2FA)
- [x] 10.2 login KO (password incorrecto, usuario inexistente)
- [x] 10.3 login con 2FA: emite pre_auth_ticket, luego verify_totp emite sesión
- [x] 10.4 refresh rotation: usar token → ok; reuso del mismo token → 401
- [x] 10.5 logout: revocar token → refresh falla
- [x] 10.6 rate limit: 5 intentos OK, 6to → 429
- [x] 10.7 recuperación: forgot emite token de un solo uso; reset con token válido; reset con token ya usado → 400
- [x] 10.8 `get_current_user`: con token válido → usuario; con parámetro URL → NUNCA acepta identidad por param
- [x] 10.9 tenant isolation: usuario de tenant A no puede usar token de tenant B
