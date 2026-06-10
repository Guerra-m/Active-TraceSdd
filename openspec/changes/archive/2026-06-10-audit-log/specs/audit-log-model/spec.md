## ADDED Requirements

### Requirement: Modelo AuditLog append-only con campos obligatorios
El sistema SHALL implementar un modelo ORM `AuditLog` que herede de `Base` (no de `TenantScopedBase`) con los campos: `id` (UUID PK), `tenant_id` (UUID FK → Tenant, NOT NULL), `fecha_hora` (DateTime con timezone, NOT NULL, default=now), `actor_id` (UUID FK → User, NOT NULL), `impersonado_id` (UUID FK → User, nullable), `materia_id` (UUID FK → Materia, nullable), `accion` (String NOT NULL), `detalle` (JSONB nullable), `filas_afectadas` (Integer nullable), `ip` (String nullable), `user_agent` (String nullable).

#### Scenario: Registro se crea con campos mínimos obligatorios
- **WHEN** se inserta un `AuditLog` con `tenant_id`, `actor_id` y `accion` presentes
- **THEN** el registro se persiste correctamente y `fecha_hora` se asigna automáticamente

#### Scenario: Registro con impersonación registra ambos actores
- **WHEN** se inserta un `AuditLog` con `actor_id` (quien impersona) e `impersonado_id` (quien es impersonado)
- **THEN** ambos campos quedan almacenados y son consultables por separado

---

### Requirement: Inmutabilidad append-only a nivel base de datos
El sistema SHALL crear un trigger PostgreSQL `BEFORE UPDATE OR DELETE ON audit_log` que ejecute `RAISE EXCEPTION 'audit_log is append-only'` rechazando toda modificación o borrado directo sobre la tabla, incluso con credenciales de la aplicación.

#### Scenario: UPDATE directo sobre audit_log falla con excepción
- **WHEN** se ejecuta `UPDATE audit_log SET accion = 'X' WHERE id = :id` via SQL crudo en la sesión de tests
- **THEN** la excepción llega a Python (ProgrammingError o similares de asyncpg) y ninguna fila resulta modificada

#### Scenario: DELETE directo sobre audit_log falla con excepción
- **WHEN** se ejecuta `DELETE FROM audit_log WHERE id = :id` via SQL crudo en la sesión de tests
- **THEN** la excepción llega a Python y ninguna fila resulta eliminada

---

### Requirement: Migración 004 crea tabla audit_log con índices y trigger
El sistema SHALL proveer una migración Alembic `20260610_004_audit_log.py` que: (1) crea la tabla `audit_log` con todos sus campos y constraints, (2) crea índices en `(tenant_id, fecha_hora DESC)` y `(tenant_id, actor_id)`, (3) crea el trigger append-only, (4) define un `downgrade()` que elimina el trigger y la tabla.

#### Scenario: alembic upgrade head aplica la migración sin errores
- **WHEN** se ejecuta `alembic upgrade head` sobre una DB con migraciones 001–003 aplicadas
- **THEN** la tabla `audit_log` existe con el trigger y los índices esperados

#### Scenario: alembic downgrade -1 revierte la migración sin errores
- **WHEN** se ejecuta `alembic downgrade -1` después de aplicar 004
- **THEN** la tabla `audit_log` y el trigger son eliminados y la DB queda en estado 003
