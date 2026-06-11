## MODIFIED Requirements

### Requirement: Tabla users extiende con campos de perfil docente via migración 006
El sistema SHALL añadir las siguientes columnas nullable a la tabla `users` en la migración 006: `nombre` (VARCHAR 200), `apellidos` (VARCHAR 200), `dni_encrypted` (TEXT), `cuil_encrypted` (TEXT), `cbu_encrypted` (TEXT), `alias_cbu_encrypted` (TEXT), `banco` (VARCHAR 100), `regional` (VARCHAR 100), `legajo` (VARCHAR 50), `legajo_profesional` (VARCHAR 50), `facturador` (BOOLEAN DEFAULT FALSE), `estado` (VARCHAR 20 CHECK IN('Activo','Inactivo') DEFAULT 'Activo'). El downgrade SHALL eliminar estas columnas vía `ALTER TABLE users DROP COLUMN`. El comportamiento de autenticación (email/password/token) NO cambia.

El endpoint `POST /api/auth/login` SHALL incluir en la respuesta el campo `requires_2fa: boolean` y, cuando sea true, un `temp_token` de corta duración para completar el flujo 2FA. El campo `access_token` SHALL estar ausente en la respuesta cuando `requires_2fa: true`.

#### Scenario: alembic upgrade 006 añade columnas sin afectar filas existentes
- **WHEN** se ejecuta `alembic upgrade head` sobre una DB con usuarios pre-existentes (filas de auth)
- **THEN** las nuevas columnas se añaden con valor NULL o DEFAULT para filas existentes; los endpoints de auth siguen funcionando sin cambio

#### Scenario: alembic downgrade revierte las columnas de perfil
- **WHEN** se ejecuta `alembic downgrade -1` después de aplicar 006
- **THEN** las columnas de perfil desaparecen de `users` y la tabla vuelve a su estado de migración 005

#### Scenario: Campos PII del perfil se almacenan cifrados y no se exponen en respuestas estándar
- **WHEN** se crea un usuario con dni "12345678"
- **THEN** la columna `dni_encrypted` en DB contiene un valor cifrado (no "12345678") y el GET /api/v1/admin/usuarios/{id} no incluye `dni` en el body de respuesta

#### Scenario: Login sin 2FA devuelve tokens directamente
- **WHEN** el usuario hace login con credenciales válidas y 2FA no está habilitado
- **THEN** la respuesta incluye `access_token`, `refresh_token` y `requires_2fa: false`

#### Scenario: Login con 2FA devuelve temp_token sin access_token
- **WHEN** el usuario hace login con credenciales válidas y 2FA está habilitado en su cuenta
- **THEN** la respuesta incluye `requires_2fa: true`, `temp_token` y NO incluye `access_token`
