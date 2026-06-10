## MODIFIED Requirements

### Requirement: Tabla users extiende con campos de perfil docente via migración 006
El sistema SHALL añadir las siguientes columnas nullable a la tabla `users` en la migración 006: `nombre` (VARCHAR 200), `apellidos` (VARCHAR 200), `dni_encrypted` (TEXT), `cuil_encrypted` (TEXT), `cbu_encrypted` (TEXT), `alias_cbu_encrypted` (TEXT), `banco` (VARCHAR 100), `regional` (VARCHAR 100), `legajo` (VARCHAR 50), `legajo_profesional` (VARCHAR 50), `facturador` (BOOLEAN DEFAULT FALSE), `estado` (VARCHAR 20 CHECK IN('Activo','Inactivo') DEFAULT 'Activo'). El downgrade SHALL eliminar estas columnas vía `ALTER TABLE users DROP COLUMN`. El comportamiento de autenticación (email/password/token) NO cambia.

#### Scenario: alembic upgrade 006 añade columnas sin afectar filas existentes
- **WHEN** se ejecuta `alembic upgrade head` sobre una DB con usuarios pre-existentes (filas de auth)
- **THEN** las nuevas columnas se añaden con valor NULL o DEFAULT para filas existentes; los endpoints de auth siguen funcionando sin cambio

#### Scenario: alembic downgrade revierte las columnas de perfil
- **WHEN** se ejecuta `alembic downgrade -1` después de aplicar 006
- **THEN** las columnas de perfil desaparecen de `users` y la tabla vuelve a su estado de migración 005

#### Scenario: Campos PII del perfil se almacenan cifrados y no se exponen en respuestas estándar
- **WHEN** se crea un usuario con dni "12345678"
- **THEN** la columna `dni_encrypted` en DB contiene un valor cifrado (no "12345678") y el GET /api/v1/admin/usuarios/{id} no incluye `dni` en el body de respuesta
