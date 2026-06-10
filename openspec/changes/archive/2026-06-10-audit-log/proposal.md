## Why

El nombre del producto es *trace* — todo audita. Sin un registro de auditoría append-only, no hay trazabilidad de quién hizo qué ni cuándo, lo que impide cumplir los requisitos de accountability de la plataforma y bloquea la impersonación permisada (soporte / ADMIN). C-04 completó el RBAC fino; C-05 añade la capa de registro que lo hace auditable.

## What Changes

- Nuevo modelo `AuditLog` (E-AUD) append-only: sin UPDATE ni DELETE a nivel aplicación ni base de datos. Campos: `actor_id`, `impersonado_id`, `tenant_id`, `materia_id` (nullable), `accion` (código estandarizado), `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`, `fecha_hora`.
- Helper `audit()` (función async) para registrar acciones significativas con código de acción estandarizado (`CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, etc.) desde cualquier capa del backend.
- Migración `004_audit_log`: crea tabla `audit_log` con restricciones de inmutabilidad a nivel DB (trigger o regla que rechaza UPDATE/DELETE).
- Endpoint `POST /api/v1/auth/impersonate` para iniciar impersonación y `DELETE /api/v1/auth/impersonate` para finalizarla, protegidos con `require_permission("impersonacion:usar")`.
- Modificación del token de acceso bajo impersonación: payload incluye `actor_id` + `impersonated_id` para que `get_current_user` y el helper de auditoría distingan la sesión.
- Tests: append-only (UPDATE/DELETE rechazados a nivel app), atribución correcta bajo impersonación, registro con código + `filas_afectadas`, aislamiento de tenant en audit log.

## Capabilities

### New Capabilities

- `audit-log-model`: Modelo ORM `AuditLog`, migración 004 con tabla append-only, restricción DB anti-UPDATE/DELETE, índices por `(tenant_id, fecha_hora)` y `(tenant_id, actor_id)`.
- `audit-helper`: Función async `audit(db, actor_id, tenant_id, accion, *, impersonado_id, materia_id, detalle, filas_afectadas, ip, user_agent)` — punto único de escritura al log; crea el registro en la sesión actual sin exponer el modelo directamente.
- `impersonation-session`: Endpoints de inicio/fin de impersonación, modificación del JWT payload, dependencia `get_impersonation_context` que extrae `actor_id` e `impersonated_id` del token, y registro automático de `IMPERSONACION_INICIAR` / `IMPERSONACION_FINALIZAR` en el audit log.

### Modified Capabilities

- `require-permission-guard`: El guard actual usa `get_current_user` que resuelve identidad del JWT. Bajo impersonación el `user_id` efectivo es el `impersonated_id`, pero el `actor_id` para auditoría es el del token real. El guard debe exponer ambos en `request.state` para que el helper de auditoría los consuma sin volver a parsear el token.

## Impact

- **Nuevo archivo**: `backend/app/models/audit_log.py`, `backend/app/repositories/audit_log_repository.py`, `backend/app/core/audit.py` (helper), `backend/app/api/v1/routers/impersonation.py`.
- **Migración**: `backend/alembic/versions/20260610_004_audit_log.py`.
- **Modificado**: `backend/app/core/security.py` (tokens con impersonación), `backend/app/core/dependencies.py` (exponer `actor_id`/`impersonated_id`), `backend/app/core/permissions.py` (propagar al `request.state`), `backend/app/main.py` (registrar router de impersonación).
- **Tests nuevos**: `tests/test_audit_log.py`, `tests/test_impersonation.py`.
- **Sin cambios en**: modelos de negocio existentes, routers de auth/health/rbac (salvo registro de router nuevo en main.py).
