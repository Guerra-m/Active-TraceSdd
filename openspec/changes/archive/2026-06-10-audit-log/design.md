## Context

El sistema necesita un registro de auditoría append-only (E-AUD) que cubra toda acción significativa. C-04 implementó RBAC fino con `require_permission`; C-05 añade la capa de registro que hace ese RBAC auditable. El log es cross-cutting: cualquier módulo futuro (calificaciones, comunicaciones, liquidaciones) escribirá en él. La impersonación es una feature de alto riesgo que exige sesión distinguible y atribución al actor real en el mismo log.

Estado actual: no existe tabla `audit_log` ni helper de escritura. La migración más reciente es `003_rbac_tables`. El token JWT actual solo transporta `sub` (user_id) y `tenant_id`; no diferencia sesiones de impersonación.

## Goals / Non-Goals

**Goals:**

- Tabla `audit_log` inmutable a nivel app y DB (no UPDATE, no DELETE).
- Helper `audit()` como único punto de escritura al log desde cualquier capa.
- Impersonación: endpoints de inicio/fin, token diferenciado, atribución correcta.
- Tests: inmutabilidad, atribución bajo impersonación, aislamiento de tenant.

**Non-Goals:**

- UI de consulta del audit log (es C-19 panel-auditoria-metricas).
- Llamadas automáticas a `audit()` desde todos los endpoints (cada módulo lo hace al implementarse; solo se crean los primeros ejemplos en este change).
- Retención / archivado / rotación del log (infraestructura fuera de alcance).
- Rate limiting de impersonación (se aplica en C global de seguridad).

## Decisions

### D-01: Inmutabilidad append-only a nivel DB con trigger PostgreSQL

**Decisión**: crear un trigger `BEFORE UPDATE OR DELETE ON audit_log` que ejecuta `RAISE EXCEPTION` y rechaza toda modificación. No depender solo de la capa ORM.

**Alternativas consideradas**:
- Solo restricción en capa app (ORM sin `update()` ni `delete()`) → insuficiente; un bug o acceso directo a DB burlaría la garantía.
- `SECURITY DEFINER` + revocar permisos de tabla → complejo con SQLAlchemy async y rotación de credenciales.
- Tabla de solo-INSERT a nivel PostgreSQL (`GRANT INSERT` sin `UPDATE/DELETE`) → requiere usuario DB separado, aumenta complejidad de CI/CD.

**Rationale**: trigger es la capa más simple que da garantía fuerte sin cambiar el modelo de credenciales.

### D-02: Helper `audit()` como función standalone (no método de modelo ni mixin)

**Decisión**: `app/core/audit.py` expone `async def audit(db: AsyncSession, ...)`. Ningún modelo llama a `audit()` internamente; lo llama quien registra la acción (router o service, según cada módulo).

**Alternativas consideradas**:
- Mixin `Auditable` con `after_flush` de SQLAlchemy → acoplamiento implícito, dificulta el control de `filas_afectadas` y el `detalle` contextual.
- Middleware global que intercepta todos los requests → demasiado genérico; no conoce semántica de cada acción ni cuántas filas afectó.

**Rationale**: función explícita que se llama con intención. Cada módulo sabe qué registrar y cuándo.

### D-03: Token JWT con campo `impersonated_id` opcional

**Decisión**: el token de impersonación añade `impersonated_id: UUID` al payload. `get_current_user` retorna al impersonado como identidad efectiva; `get_actor_id` retorna al actor real desde el mismo token. El campo `impersonated_id` ausente o `null` → sesión normal.

**Alternativas consideradas**:
- Header `X-Impersonate-As` en cada request → trivialmente falsificable por cualquier cliente; viola regla dura #8.
- Sesión DB separada para impersonación → complejidad desproporcionada al scope.

**Rationale**: el JWT es la fuente de verdad de identidad (regla dura #8). El campo extra en el payload mantiene el modelo coherente sin nueva infraestructura.

### D-04: Migración 004 — nombre `20260610_004_audit_log`

Las migraciones existentes son 001, 002, 003. CHANGES.md menciona "Migración 003" para este change, pero 003 fue usada por C-04 RBAC. Se usa 004 para mantener la secuencia correcta.

### D-05: `AuditLog` hereda de `Base` (no de `TenantScopedBase`)

`TenantScopedBase` añade soft-delete y campos `deleted_at`. El audit log nunca se borra; soft delete no aplica. Hereda de `Base` directamente y lleva `tenant_id` como FK explícita sin el mixin de soft-delete.

### D-06: `RolPermisoRepository` no filtra `audit_log` por tenant en lectura (solo en escritura)

La lectura del audit log (futura, C-19) requiere scope de tenant; la escritura también. El `AuditLogRepository` expondrá solo `insert()` — sin `get()`, `list()` ni `delete()` — para que sea imposible errar en la dirección de append-only.

## Risks / Trade-offs

- **[Riesgo] Trigger falla silencioso en test CI** → Mitigación: el test `test_audit_log.py::test_update_raises` intenta un `UPDATE` directo via SQL crudo y verifica que la excepción llega a Python. Si el trigger no existe, el test falla y bloquea el merge.
- **[Riesgo] Token de impersonación con `impersonated_id` puede causar confusión en `get_current_user`** → Mitigación: `get_current_user` retorna siempre el usuario **efectivo** (impersonado si existe, propio si no). El `actor_id` se expone por separado en `request.state.actor_id`. Está documentado en el spec de `impersonation-session`.
- **[Trade-off] `audit()` es explícito (no automático)** → ventaja: control total del desarrollador sobre qué se registra y con qué `detalle`. Desventaja: se puede olvidar llamarlo. Mitigación: checklist en tasks + code-review.
- **[Riesgo] Migración downgrade borra el log** → Mitigación: el downgrade de 004 hace `DROP TABLE audit_log IF EXISTS`; documentado. En producción el downgrade de auditoría requerirá aprobación manual explícita.

## Migration Plan

1. Aplicar `alembic upgrade head` (agrega `004_audit_log` con trigger).
2. No hay datos a migrar (tabla nueva).
3. Rollback: `alembic downgrade -1` elimina la tabla — solo aceptable en dev/staging, no en producción con datos.
