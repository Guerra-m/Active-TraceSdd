# Design — auth-jwt-2fa (C-03)

## Decisiones de diseño

### D1 — Email cifrado, no en plaintext
El email de usuario se almacena cifrado con AES-256-GCM (usando `app/core/encryption.py`). Para búsqueda por email, se agrega `email_hash` (SHA-256 del email normalizado) como columna indexada. Esto permite lookup O(1) sin exponer el email en la DB.

### D2 — Refresh token: solo el hash en DB
El valor crudo del refresh token nunca toca la base de datos. Se guarda el hash SHA-256. El token crudo viaja solo en la respuesta HTTP. Al validar, se hashea lo recibido y se compara contra la DB.

### D3 — 2FA TOTP: ticket temporal entre credenciales y sesión
Si `totp_enabled=True`, el login exitoso emite un `pre_auth_ticket` (JWT corto de 5min, claim `type=pre_auth`). El cliente debe llamar `/api/auth/totp/verify` con ese ticket + el código TOTP para obtener la sesión real. Nunca se emite access/refresh si el 2FA no fue completado.

### D4 — Rate limiting en memoria (por ahora)
Rate limit 5/60s por clave `{ip}:{email_hash}` usando un dict en memoria con sliding window. En producción se reemplaza por Redis, pero para esta fase la implementación in-memory es suficiente y no introduce nueva infraestructura.

### D5 — `get_current_user`: identidad solo del JWT
La dependency extrae `user_id`, `tenant_id` y `roles` del payload del JWT verificado. Nunca lee un header `X-User-ID` ni ningún parámetro de request. El token se toma de `Authorization: Bearer <token>`.

### D6 — RefreshToken y PasswordResetToken NO heredan TenantScopedBase
Estos modelos tienen `tenant_id` pero su lifecycle es cross-tenant administrativo (un token puede revocarse globalmente). Heredan `Base` directamente y tienen `tenant_id` como columna explícita para cumplir el requisito de row-level tenancy sin el mixin.

### D7 — TOTP secret cifrado en DB
El `totp_secret` se almacena cifrado con AES-256-GCM. Solo se descifra en memoria al momento de validar el código.

## Flujo de login (con 2FA)

```
POST /auth/login
  1. Buscar usuario por email_hash (lookup eficiente)
  2. Verificar password con Argon2id
  3. Verificar rate limit (5/60s por IP+email)
  4. Si totp_enabled=False → emitir access + refresh → FIN
  5. Si totp_enabled=True  → emitir pre_auth_ticket → cliente llama /totp/verify

POST /auth/totp/verify (con pre_auth_ticket en Bearer)
  1. Verificar pre_auth_ticket (type=pre_auth, no expirado)
  2. Verificar código TOTP contra secret descifrado
  3. Emitir access + refresh token
```

## Flujo de refresh rotation

```
POST /auth/refresh (con refresh token en body)
  1. Hashear el refresh token recibido
  2. Buscar en DB por hash
  3. Verificar: no revocado, no expirado, tenant activo
  4. Revocar el refresh token viejo (revoked_at = now)
  5. Emitir nuevo par access + refresh
  Nota: si el mismo token se usa dos veces → la segunda vez falla (token ya revocado)
```

## Estructura de capas

```
Router (auth.py)
  └─ AuthService (auth_service.py)
       ├─ UserRepository (user_repository.py)
       ├─ RefreshTokenRepository (refresh_token_repository.py)
       └─ core/security.py (hash, JWT, TOTP)
```

Regla: nunca acceso directo a DB desde routers ni services. Todo via repository.

## Schemas Pydantic (request/response)

```
LoginRequest:      email: str, password: str, totp_code: str | None
LoginResponse:     access_token: str, refresh_token: str, token_type: str
PreAuthResponse:   pre_auth_ticket: str  (cuando 2FA está activo)
RefreshRequest:    refresh_token: str
LogoutRequest:     refresh_token: str
TotpEnrollResponse: secret: str, qr_uri: str
TotpVerifyRequest:  pre_auth_ticket: str, code: str
ForgotRequest:     email: str
ResetRequest:      token: str, new_password: str
```

Todos los schemas: `model_config = ConfigDict(extra='forbid')`
