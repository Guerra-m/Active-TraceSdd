## 1. TenantScopedBase mixin y modelo Tenant

- [x] 1.1 (RED) Escribir `tests/test_tenant_model.py`: test que verifica que una clase que hereda `TenantScopedBase` tiene columnas `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`; y que `id` se genera como UUID v4 automáticamente
- [x] 1.2 (GREEN) Crear `app/models/base.py` con `TenantScopedBase` mixin: `id` (UUID PK, default=uuid4), `tenant_id` (UUID, FK → `tenants.id`, NOT NULL, indexed), `created_at` (UTC, auto), `updated_at` (UTC, auto-update), `deleted_at` (UTC, nullable)
- [x] 1.3 (TRIANGULATE) Agregar casos: `tenant_id` nulo levanta `IntegrityError`, `updated_at` cambia al modificar, dos instancias generan UUIDs distintos
- [x] 1.4 (RED) Escribir test para modelo `Tenant`: instanciación con `name`/`slug`, `is_active=True` por defecto, unicidad de `slug` levanta `IntegrityError`
- [x] 1.5 (GREEN) Crear `app/models/tenant.py` con clase `Tenant(Base)` (sin mixin — `Tenant` es la raíz): columnas `id`, `name`, `slug`, `is_active`, `created_at`, `updated_at`

## 2. Utilidad de cifrado AES-256-GCM

- [x] 2.1 Agregar `cryptography` a dependencias en `pyproject.toml` (si no está ya)
- [x] 2.2 (RED) Escribir `tests/test_encryption.py`: test round-trip `encrypt → decrypt`, test que dos cifrados del mismo texto dan ciphertext distinto, test que ciphertext alterado levanta excepción de integridad
- [x] 2.3 (GREEN) Implementar `app/core/encryption.py` con funciones `encrypt(plaintext: str) -> str` y `decrypt(ciphertext: str) -> str` usando AES-256-GCM; nonce de 12 bytes random por operación; serializar como `b64(nonce):b64(tag+ciphertext)` en columna TEXT
- [x] 2.4 (TRIANGULATE) Agregar caso: `ENCRYPTION_KEY` inválida (longitud incorrecta) en `Settings` levanta `ValidationError` antes de que la app arranque; `decrypt()` con ciphertext truncado lanza `InvalidTag`
- [x] 2.5 Actualizar `core/config.py`: agregar validador Pydantic que verifica que `ENCRYPTION_KEY` tiene exactamente 32 bytes (puede estar en base64 o hex, documentar en `.env.example`)

## 3. Repository base con scope de tenant

- [x] 3.1 (RED) Escribir `tests/test_base_repository.py`: preparar dos tenants y una tabla de dominio de prueba (modelo auxiliar para el test); verificar que el repository del tenant A no ve registros del tenant B
- [x] 3.2 (GREEN) Crear `app/repositories/base.py` con `BaseRepository[T]`: `__init__(session, tenant_id)`, métodos `get_by_id`, `list(offset, limit)`, `create`, `update`, `soft_delete`; todos los SELECTs filtran `tenant_id = self.tenant_id AND deleted_at IS NULL`; `create` inyecta `tenant_id` automáticamente
- [x] 3.3 (TRIANGULATE) Agregar casos: `soft_delete` de ID inexistente retorna `False`; `list()` no devuelve registros con `deleted_at IS NOT NULL`; `create` sin `tenant_id` explícito resulta en registro con `tenant_id` del repo; `BaseRepository` sin `tenant_id` levanta `TypeError`
- [x] 3.4 (REFACTOR) Revisar que no existe ningún método en `BaseRepository` que ejecute un query sin filtro de tenant; si existe, eliminarlo

## 4. Migración Alembic 001

- [x] 4.1 Actualizar `alembic/env.py` para importar `Base` de `app.core.database` y ejecutar migraciones con `AsyncEngine` (usando `run_sync` wrapper de Alembic para async)
- [x] 4.2 Crear migración manual `alembic/versions/20260610_001_create_tenants.py` siguiendo la convención `YYYYMMDD_NNN_descripcion`; `upgrade()` crea tabla `tenants` con todas sus columnas y constraints; `downgrade()` la elimina con `DROP TABLE tenants`
- [x] 4.3 Verificar que `alembic upgrade head` aplicado contra la DB de test crea la tabla `tenants` correctamente; verificar con `alembic current` que la revisión es la esperada
- [x] 4.4 Verificar que `alembic downgrade base` elimina la tabla y deja la BD limpia

## 5. Actualización de conftest.py y fixtures de integración

- [x] 5.1 Actualizar `tests/conftest.py`: agregar fixture `test_tenant` que crea y persiste un `Tenant` de prueba con `slug="test-tenant"` en la DB de test; agregar fixture `test_tenant_b` para tests de aislamiento multi-tenant
- [x] 5.2 Asegurar que la fixture de sesión de DB de test aplica las migraciones (o crea las tablas desde `Base.metadata.create_all`) antes de los tests y hace `DROP` al finalizar

## 6. Verificación final e integración

- [x] 6.1 Ejecutar la suite completa de tests (`pytest`) y confirmar que todos los tests existentes (C-01: health, database, config, startup) siguen en verde junto con los nuevos tests de C-02
- [x] 6.2 Confirmar que ningún archivo `.py` creado supera 500 LOC
- [x] 6.3 Verificar con `alembic check` (o `alembic revision --autogenerate --sql`) que no hay cambios pendientes de schema tras aplicar la migración 001 con `Tenant` registrado en `Base.metadata`
