## Why

El sistema necesita una capa de autenticación segura como prerequisito para todo el resto del producto: sin identidad verificada no hay multi-tenancy real, ni RBAC, ni auditoría. C-02 dejó los stubs (`security.py`, `tenancy.py`, `dependencies.py`) listos para ser completados — este change los llena con la implementación real.

## What Changes

- `POST /api/auth/login` — autentica con email + password (Argon2id), emite JWT access (15min) + refresh con rotación
- `POST /api/auth/refresh` — rota el refresh token (el viejo se revoca), emite nuevo par
- `POST /api/auth/logout` — revoca la sesión (invalida el refresh token activo)
- **2FA TOTP opcional**: enrolar (`POST /api/auth/totp/enroll`), verificar (`POST /api/auth/totp/verify`) — gate entre credenciales válidas y emisión de sesión completa
- Recuperación de contraseña: `POST /api/auth/forgot` (token de un solo uso, 1h) + `POST /api/auth/reset`
- Rate limiting 5 intentos/60s por IP+email en el endpoint de login
- Dependency `get_current_user` que resuelve identidad + tenant SIEMPRE del JWT verificado
- Modelos ORM: `User`, `RefreshToken`, `PasswordResetToken`
- Migración Alembic 002 con las tres tablas

## Capabilities

### New Capabilities
- `user-model`: Modelo ORM User con email cifrado AES-256, password Argon2id, TOTP opcional
- `auth-tokens`: Modelos RefreshToken y PasswordResetToken; lógica de rotación y revocación
- `auth-endpoints`: Router `/api/auth/*` con login, refresh, logout, TOTP, recuperación
- `auth-service`: Servicio de autenticación con rate limiting, validaciones, emisión de tokens
- `auth-dependency`: Dependency `get_current_user` que extrae identidad del JWT verificado

### Modified Capabilities
- (ninguna — las capabilities anteriores estaban en stub, no tenían spec)

## Impact

- **Archivos nuevos**: `app/models/user.py`, `app/models/refresh_token.py`, `app/models/password_reset_token.py`, `app/repositories/user_repository.py`, `app/repositories/refresh_token_repository.py`, `app/services/auth_service.py`, `app/api/v1/routers/auth.py`, `app/schemas/auth.py`
- **Archivos modificados**: `app/core/security.py` (stub → implementación), `app/core/tenancy.py` (stub → implementación), `app/core/dependencies.py` (agregar `get_current_user`), `app/core/config.py` (agregar `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Migración**: `alembic/versions/20260610_002_auth_tables.py`
- **Tests**: `tests/test_auth.py` — suite completa TDD
- **Dependencias ya instaladas**: `argon2-cffi`, `python-jose[cryptography]`, `pyotp` (agregar)
