## Why

El esqueleto FastAPI (C-01) existe, pero el sistema aún no puede persistir datos de dominio: falta el modelo `Tenant` raíz, el mixin base que garantiza UUID + timestamps + soft delete en cada tabla, el repository genérico con scope de tenant siempre activo, y la utilidad de cifrado AES-256 para los atributos `[cifrado]` del modelo de datos. Sin estos cimientos, ningún change de dominio (usuarios, materias, calificaciones, etc.) puede arrancar de forma segura ni consistent. Es el prerrequisito del camino crítico.

## What Changes

- **Nuevo modelo `Tenant`**: entidad raíz del sistema; cada institución es un tenant aislado.
- **`TenantScopedBase` mixin**: `id` (UUID v4, server-side), `tenant_id` (FK → Tenant, NOT NULL), `created_at`, `updated_at`, `deleted_at` (soft delete). Todo modelo de dominio hereda de este mixin.
- **`BaseRepository[T]` genérico**: CRUD con `tenant_id` en TODOS los queries por defecto. Un query sin scope de tenant no puede ejecutarse — falla en review y en runtime por diseño.
- **Utilidad de cifrado AES-256** (`core/encryption.py`): cifrado/descifrado en reposo para atributos marcados `[cifrado]` (email, DNI, CUIL, CBU). Nunca en logs, nunca en texto plano fuera del proceso.
- **Migración Alembic 001**: crea la tabla `tenants` y establece la convención `YYYYMMDD_NNN_descripcion` para todas las migraciones futuras.
- **Soft delete transversal**: `deleted_at IS NULL` incluido automáticamente en todas las queries del repository base; el método `soft_delete()` setea el timestamp sin borrar el registro.
- **Tests**: aislamiento multi-tenant (un tenant no accede a datos de otro), soft delete, cifrado round-trip, mixin de timestamps automáticos.

## Capabilities

### New Capabilities
- `tenant-model`: Entidad `Tenant` raíz, mixin `TenantScopedBase` y convención UUID para todas las entidades de dominio.
- `tenant-repository`: `BaseRepository[T]` genérico con scope de tenant siempre activo, soft delete integrado y helpers CRUD async.
- `encryption-utils`: Utilidad AES-256 (`core/encryption.py`) para cifrado/descifrado en reposo de atributos PII; sin exposición en logs.
- `alembic-migration-001`: Migración inicial de schema (tabla `tenants`) y convención de naming para migraciones futuras.

### Modified Capabilities
- `database-connection`: El `Base` declarativo de SQLAlchemy se extiende para que los modelos hereden de `TenantScopedBase` automáticamente al registrarse.

## Impact

- **Backend**: nuevos archivos `app/models/tenant.py`, `app/models/base.py`, `app/repositories/base.py`, `app/core/encryption.py`; modificación de `alembic/env.py` para registrar el metadata del mixin; nueva migración `alembic/versions/20260610_001_create_tenants.py`.
- **Tests**: nuevos `tests/test_tenant_model.py`, `tests/test_base_repository.py`, `tests/test_encryption.py`; actualización de `conftest.py` para fixtures de tenant de test.
- **Dependencias**: librería `cryptography` (ya disponible en Python) para AES-GCM; `uuid` (stdlib). Sin nuevas dependencias externas.
- **Changes bloqueados desbloqueados**: C-03 (auth-jwt-2fa), C-04 (rbac), C-05 (audit-log) y todos los módulos de dominio pueden arrancar una vez aprobado este change.
