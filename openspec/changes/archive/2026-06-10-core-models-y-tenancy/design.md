## Context

C-01 (foundation-setup) entregó el esqueleto FastAPI con conexión async a PostgreSQL, `Base` declarativa de SQLAlchemy, Alembic inicializado y slots de `core/` reservados. El sistema puede arrancar y responder al health-check, pero ninguna tabla de dominio existe aún.

Este change introduce la capa de persistencia fundacional: el modelo `Tenant`, el mixin que todo modelo de dominio hereda, el repository genérico con scope de tenant, la utilidad de cifrado para PII y la primera migración de Alembic. Es el cimiento sobre el que se construyen C-03 (auth), C-04 (rbac), C-05 (audit-log) y todos los módulos de dominio.

Governance: CRÍTICO. Toda decisión de este change afecta la seguridad de aislamiento entre tenants para toda la vida del sistema.

## Goals / Non-Goals

**Goals:**
- Definir `Tenant` como entidad raíz del sistema (tabla `tenants`).
- Proveer `TenantScopedBase` mixin que todo modelo de dominio hereda: `id` UUID v4, `tenant_id` FK, `created_at`, `updated_at`, `deleted_at`.
- Implementar `BaseRepository[T]` genérico con scope de tenant en TODOS los queries por defecto; soft delete automático.
- Implementar `core/encryption.py` con AES-256-GCM para cifrar/descifrar atributos `[cifrado]`; resultado Base64-encoded para almacenamiento en columnas TEXT.
- Migración Alembic 001 que crea la tabla `tenants` y establece la convención de naming.
- Tests con base de datos real de test (sin mocks de DB).

**Non-Goals:**
- Modelos de dominio concretos (Usuario, Materia, etc.) — esos son C-03 en adelante.
- RBAC ni lógica de autenticación — son C-03 y C-04.
- Resolución del `tenant_id` desde el JWT en dependencias FastAPI — es C-03.
- Cifrado de columnas a nivel de base de datos (pgcrypto) — se usa cifrado en capa de aplicación por simplicidad y portabilidad.

## Decisions

### D1: Mixin vs. herencia de clase base de SQLAlchemy

**Decisión**: `TenantScopedBase` es un mixin Python puro (sin `__tablename__`, sin mapper config propia) que los modelos concretos usan junto con la `Base` declarativa de SQLAlchemy.

**Alternativa descartada**: Una clase base ORM abstracta (`__abstract__ = True`). Genera conflictos con Alembic autogenerate cuando hay múltiples niveles de herencia.

**Rationale**: El mixin puro permite combinar flexiblemente con la `Base` de C-01 sin alterar la herencia ORM. Alembic detecta las columnas del mixin correctamente en cada tabla concreta.

### D2: UUID generado server-side en Python, no en la BD

**Decisión**: `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)` — el UUID se genera en Python al crear la instancia.

**Alternativa descartada**: `server_default=text("gen_random_uuid()")` (PostgreSQL). Requiere extensión `pgcrypto` o PostgreSQL ≥13 con `uuid-ossp`; complica los tests con fixtures sin `RETURNING`.

**Rationale**: Generación en Python es suficientemente aleatoria, portabl y testeable sin depender de funciones de la BD.

### D3: AES-256-GCM con clave derivada de ENCRYPTION_KEY de Settings

**Decisión**: Se usa `cryptography.hazmat.primitives.ciphers.aead.AESGCM` con nonce de 12 bytes random por cada operación de cifrado. El resultado se serializa como `nonce_b64:ciphertext_b64` en una sola cadena Base64.

**Alternativa descartada**: Fernet (AES-128-CBC + HMAC). Fernet es más simple pero AES-128 no cumple el requisito AES-256 del PRD. Fernet además incluye timestamp de expiración que no necesitamos.

**Rationale**: AES-256-GCM provee confidencialidad + autenticidad (AEAD). El nonce random por operación evita reutilización. La serialización `nonce:ciphertext` en una columna TEXT es auto-contenida (sin tabla auxiliar).

### D4: BaseRepository con `tenant_id` inyectado como parámetro, no desde contexto global

**Decisión**: `BaseRepository.__init__(self, session: AsyncSession, tenant_id: UUID)` — el `tenant_id` se pasa explícitamente en construcción.

**Alternativa descartada**: Obtener `tenant_id` de un `ContextVar` (contexto de request). Los ContextVar introducen estado implícito difícil de testar y rastrear.

**Rationale**: Explícito > implícito. El `tenant_id` queda visible en cada instanciación del repository. En C-03, la dependency FastAPI construirá el repository pasando el `tenant_id` del JWT verificado.

### D5: Soft delete con `deleted_at` timestamp, filtrando automáticamente en BaseRepository

**Decisión**: Todos los métodos de consulta del `BaseRepository` incluyen `WHERE deleted_at IS NULL` automáticamente. El método `soft_delete()` setea `deleted_at = datetime.utcnow()`. No existe método `hard_delete()` en el repository base.

**Rationale**: Cumple la regla dura de auditoría append-only. El historial completo se preserva. Para queries administrativos que necesiten ver registros eliminados, se puede añadir un método `get_including_deleted()` explícito en el futuro.

## Risks / Trade-offs

- **[Riesgo] ENCRYPTION_KEY ausente o de longitud incorrecta** → La inicialización de `Settings` valida que `ENCRYPTION_KEY` tenga exactamente 32 bytes (256 bits). Si la variable falta o tiene longitud incorrecta, la app no arranca. Esto es intencional: fail-fast en startup.

- **[Riesgo] Migración 001 aplicada en BD existente con extensiones** → La tabla `tenants` es nueva; no hay conflicto con C-01 que no creó tablas de dominio. Rollback: `alembic downgrade -1` borra la tabla `tenants`.

- **[Trade-off] Cifrado en capa de aplicación vs. cifrado de columna en BD** → Elegimos capa de aplicación. Consecuencia: las columnas cifradas no son buscables por valor (solo por UUID o índices no sensibles). Para activia-trace esto es aceptable dado que los atributos `[cifrado]` (DNI, CBU, email PII) no son criterio de búsqueda directo en el dominio conocido.

- **[Trade-off] `tenant_id` en mixin como NOT NULL (non-nullable por defecto)** → No hay entidad de dominio que no pertenezca a un tenant. La única excepción es `Tenant` mismo, que no hereda del mixin.

## Migration Plan

1. Asegurarse de que `ENCRYPTION_KEY` de 32 bytes esté en `.env` (ya documentado en `.env.example` desde C-01).
2. Ejecutar `alembic upgrade head` — aplica migración 001 y crea tabla `tenants`.
3. Verificar con `alembic current` que la revisión apunta a `001`.
4. **Rollback**: `alembic downgrade base` borra la tabla `tenants` (sin datos de dominio aún, seguro).

## Open Questions

- ¿El `Tenant` necesita campos adicionales en este change (nombre, slug, configuración)? Por ahora: `id`, `name`, `slug` (único), `is_active`, timestamps. La configuración por-tenant compleja se aplaza a un change dedicado.
- ¿Se necesita un endpoint de administración de tenants en este change? No — C-02 solo crea el modelo y el repository. El CRUD de tenants es parte de C-04 (admin).
