# Tasks — audit-log (C-05)

## 1. Modelo ORM y migración

- [x] 1.1 `app/models/audit_log.py` — `AuditLog` hereda de `Base` (no `TenantScopedBase`); campos: `id` (UUID PK), `tenant_id` (UUID FK Tenant NOT NULL), `fecha_hora` (DateTime TZ, default=now), `actor_id` (UUID FK User NOT NULL), `impersonado_id` (UUID FK User nullable), `materia_id` (UUID FK Materia nullable), `accion` (String NOT NULL), `detalle` (JSONB nullable), `filas_afectadas` (Integer nullable), `ip` (String nullable), `user_agent` (String nullable)
- [x] 1.2 Registrar `AuditLog` en `app/models/__init__.py`
- [x] 1.3 `alembic/versions/20260610_004_audit_log.py` — crea tabla `audit_log` con todos los campos, índices `(tenant_id, fecha_hora DESC)` y `(tenant_id, actor_id)`, y el trigger `BEFORE UPDATE OR DELETE` que hace `RAISE EXCEPTION 'audit_log is append-only'`
- [x] 1.4 Verificar que `alembic upgrade head` aplica sin errores y que `alembic downgrade -1` revierte limpiamente

## 2. Repository y helper de auditoría

- [x] 2.1 `app/repositories/audit_log_repository.py` — `AuditLogRepository` con un único método público `async insert(audit_log: AuditLog) -> None`; sin métodos `get`, `list`, `update` ni `delete`
- [x] 2.2 `app/core/audit.py` — función `async audit(db, actor_id, tenant_id, accion, *, impersonado_id=None, materia_id=None, detalle=None, filas_afectadas=None, ip=None, user_agent=None) -> None`; crea `AuditLog` y llama a `AuditLogRepository.insert()` sin hacer commit
- [x] 2.3 Definir constantes de acción en `app/core/audit.py`: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`

## 3. Token JWT de impersonación y get_current_user

- [x] 3.1 `app/core/security.py` — modificar `create_access_token` para aceptar `impersonated_id: UUID | None = None`; incluirlo en el payload solo cuando no sea `None` (campo `impersonated_id`)
- [x] 3.2 `app/core/dependencies.py` — modificar `get_current_user` para: si el token tiene `impersonated_id`, retornar el user con ese id (identidad efectiva); siempre guardar `actor_id` en `request.state.actor_id` (= `sub` del token, el actor real)
- [x] 3.3 `app/core/permissions.py` — propagar `actor_id` de `request.state` al estado ya existente; verificar que `request.state.actor_id` está disponible al momento en que `require_permission` corre

## 4. Endpoints de impersonación

- [x] 4.1 `app/schemas/impersonation.py` — `ImpersonateRequest(user_id: UUID)` con `model_config = ConfigDict(extra='forbid')` y `ImpersonateResponse(access_token: str, token_type: str)`
- [x] 4.2 `app/api/v1/routers/impersonation.py` — `POST /api/v1/auth/impersonate` protegido con `require_permission("impersonacion:usar")`; valida que el usuario objetivo existe en el mismo tenant; emite token con `impersonated_id`; registra `IMPERSONACION_INICIAR` via `audit()`
- [x] 4.3 `DELETE /api/v1/auth/impersonate` en el mismo router — acepta token de impersonación (verifica que tenga `impersonated_id`, sino 400); registra `IMPERSONACION_FINALIZAR` via `audit()`; retorna 204
- [x] 4.4 Registrar router de impersonación en `app/main.py` con prefijo `/api/v1/auth` y tag `impersonation`

## 5. Tests (TDD — Strict)

- [x] 5.1 `tests/test_audit_log.py` — safety net: correr suite base; RED: `test_insert_creates_record` escribe via `audit()` y verifica con SELECT crudo; GREEN: mínimo; triangulación: campos opcionales
- [x] 5.2 `test_audit_log.py` — `test_update_raises`: intentar UPDATE crudo en tabla → verifica excepción Python (trigger append-only activo)
- [x] 5.3 `test_audit_log.py` — `test_delete_raises`: intentar DELETE crudo en tabla → verifica excepción Python
- [x] 5.4 `test_audit_log.py` — `test_audit_helper_minimal`: llamada con parámetros mínimos → registro con campos opcionales en None
- [x] 5.5 `test_audit_log.py` — `test_audit_helper_full`: llamada con todos los parámetros → registro completo con todos los campos
- [x] 5.6 `test_audit_log.py` — `test_tenant_isolation`: registros de tenant A no aparecen en consultas de tenant B (SELECT directo por tenant_id)
- [x] 5.7 `tests/test_impersonation.py` — `test_impersonate_as_admin_returns_token`: ADMIN con `impersonacion:usar` → 200 con token válido que tiene `impersonated_id`
- [x] 5.8 `test_impersonation.py` — `test_impersonate_without_permission_returns_403`: TUTOR sin permiso → 403
- [x] 5.9 `test_impersonation.py` — `test_impersonate_cross_tenant_returns_404`: usuario de otro tenant → 404
- [x] 5.10 `test_impersonation.py` — `test_impersonate_logs_iniciar`: después de `POST /impersonate` exitoso, existe registro `IMPERSONACION_INICIAR` en `audit_log` con `actor_id` = ADMIN e `impersonado_id` = objetivo
- [x] 5.11 `test_impersonation.py` — `test_end_impersonation_returns_204`: `DELETE /impersonate` con token de impersonación → 204 y registro `IMPERSONACION_FINALIZAR`
- [x] 5.12 `test_impersonation.py` — `test_end_impersonation_with_normal_token_returns_400`: token sin `impersonated_id` → 400
- [x] 5.13 `test_impersonation.py` — `test_get_current_user_resolves_impersonated`: con token de impersonación, endpoint que usa `get_current_user` retorna datos del usuario impersonado; `request.state.actor_id` es el actor real
- [x] 5.14 `test_impersonation.py` — `test_action_under_impersonation_attributed_to_actor`: acción que llama a `audit()` bajo impersonación genera registro con `actor_id` = actor real e `impersonado_id` = impersonado
