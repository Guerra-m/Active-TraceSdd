# Tasks — rbac-permisos-finos (C-04)

## 1. Modelos ORM

- [x] 1.1 `app/models/rol.py` — `Rol` con `code` (unique), `name`, `is_system` (bool), `tenant_id` (nullable para roles sistema), `is_active`, timestamps; hereda `Base` (no `TenantScopedBase`)
- [x] 1.2 `app/models/permiso.py` — `Permiso` con `code` (unique, formato `modulo:accion`), `description`, `is_active`, `created_at`; hereda `Base`
- [x] 1.3 `app/models/rol_permiso.py` — `RolPermiso` con `rol_id` (FK), `permiso_id` (FK), `tenant_id`, `is_own_resource` (bool, default False); UNIQUE `(rol_id, permiso_id, tenant_id)`; hereda `TenantScopedBase`
- [x] 1.4 `app/models/usuario_rol.py` — `UsuarioRol` con `user_id` (FK), `rol_id` (FK), `tenant_id`, `valid_from DATE NOT NULL`, `valid_until DATE` (nullable); hereda `TenantScopedBase`; SIN soft delete (la vigencia es el mecanismo de expiración)
- [x] 1.5 Registrar los 4 modelos en `app/models/__init__.py`

## 2. Migración Alembic 003

- [x] 2.1 `alembic/versions/20260610_003_rbac_tables.py` — crear tablas `roles`, `permisos`, `rol_permiso`, `usuario_rol` con todos los índices: `(user_id, tenant_id, valid_from, valid_until)` en `usuario_rol`; `(rol_id, tenant_id)` en `rol_permiso`
- [x] 2.2 Seed en la migración: INSERT de los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) con `is_system=True`, `tenant_id=NULL`
- [x] 2.3 Seed en la migración: INSERT de todos los permisos del dominio (mínimo 21 permisos según spec `rbac-catalog`)
- [x] 2.4 Seed en la migración: INSERT de la matriz `rol_permiso` base según `knowledge-base/03_actores_y_roles.md §3.3`, con `is_own_resource` correcto para permisos marcados `(propio)`
- [x] 2.5 Verificar que `alembic downgrade -1` borra las 4 tablas limpiamente (rollback)

## 3. Repositories

- [x] 3.1 `app/repositories/rol_repository.py` — `RolRepository(BaseRepository[Rol])` con `get_by_code(code)`, `list_active(include_system=True)`; filtra por `tenant_id` del constructor para roles custom; incluye roles sistema (`tenant_id=NULL`) siempre
- [x] 3.2 `app/repositories/permiso_repository.py` — `PermisoRepository` con `get_by_code(code)`, `list_active()`
- [x] 3.3 `app/repositories/rol_permiso_repository.py` — `RolPermisoRepository` con `get_permisos_for_rol(rol_id)` → lista de `(permiso_code, is_own_resource)`
- [x] 3.4 `app/repositories/usuario_rol_repository.py` — `UsuarioRolRepository` con `get_vigentes(user_id, date=today)` → lista de `UsuarioRol` cuya vigencia cubre la fecha dada

## 4. RbacService

- [x] 4.1 `app/services/rbac_service.py` — `RbacService` con `get_effective_permissions(user_id: UUID, tenant_id: UUID, db: AsyncSession, date=today) -> set[tuple[str, bool]]`
- [x] 4.2 La query de `get_effective_permissions` usa un JOIN eficiente: `usuario_rol → rol_permiso → permisos`, filtrando por `tenant_id`, `user_id` y vigencia de `usuario_rol`
- [x] 4.3 Lógica de unión: si el mismo `permiso_code` aparece con `is_own_resource=True` y `False`, el resultado es `(code, False)` (global prevalece)

## 5. core/permissions.py y core/dependencies.py

- [x] 5.1 `app/core/permissions.py` — implementar `require_permission(code: str) -> Callable` que retorna una dependency FastAPI; la dependency llama a `RbacService.get_effective_permissions`, verifica si `code` está en el set; si no → `raise HTTPException(403, f"Permiso insuficiente: {code}")`
- [x] 5.2 Cachear resultado de `get_effective_permissions` en `request.state.rbac_permissions` para reutilización dentro del mismo request
- [x] 5.3 Exponer `permission_is_own_resource` en `request.state` cuando el permiso existe, para uso en el Service layer
- [x] 5.4 Actualizar `app/core/dependencies.py` — agregar `require_permission` como export público (importado de `core/permissions.py`)

## 6. Schemas Pydantic

- [x] 6.1 `app/schemas/rbac.py` — schemas: `RolResponse(id, code, name, is_system, is_active)`, `PermisoResponse(id, code, description)`, `RolPermisoResponse(permiso, is_own_resource)`, `UsuarioRolResponse(rol, valid_from, valid_until)` — todos con `model_config = ConfigDict(extra='forbid')`

## 7. Router de catálogo RBAC

- [x] 7.1 `app/api/v1/routers/rbac.py` — `GET /roles` protegido con `require_permission("roles:ver")` → lista roles activos del tenant + sistema
- [x] 7.2 `GET /roles/{rol_id}/permisos` protegido con `require_permission("roles:ver")` → permisos del rol con `is_own_resource`
- [x] 7.3 Registrar router en `app/main.py` con prefijo `/api/v1/rbac` y tag `rbac`

## 8. Tests (TDD — Strict)

- [x] 8.1 `tests/test_rbac_catalog.py` — seed correcto: 7 roles en DB, ≥21 permisos, matriz `rol_permiso` con `is_own_resource` correcto para PROFESOR (calificaciones:importar = True) y COORDINADOR (= False)
- [x] 8.2 `tests/test_rbac_permissions.py` — usuario sin roles → set vacío; usuario con un rol → permisos del rol; usuario con dos roles → unión correcta
- [x] 8.3 Permiso global prevalece sobre `is_own_resource=True` cuando el mismo permiso aparece en dos roles del usuario
- [x] 8.4 Asignación con `valid_until` en el pasado → NO aparece en permisos efectivos
- [x] 8.5 Asignación con `valid_from` en el futuro → NO aparece en permisos efectivos
- [x] 8.6 `tests/test_require_permission.py` — usuario con permiso → endpoint responde 200; usuario sin permiso → 403 con body correcto
- [x] 8.7 Usuario no autenticado → 401 (el guard de autenticación actúa antes del de permiso)
- [x] 8.8 `request.state.permission_is_own_resource` es `True` para PROFESOR en endpoint `calificaciones:importar` y `False` para COORDINADOR en el mismo endpoint
- [x] 8.9 Aislamiento de tenant: usuario de tenant A no puede usar roles/permisos de tenant B
- [x] 8.10 `tests/test_rbac_router.py` — GET `/api/v1/rbac/roles` con usuario ADMIN → 200 con lista; sin permiso `roles:ver` → 403
- [x] 8.11 Cache de request: verificar que con dos `require_permission` en el mismo endpoint se hace exactamente una query a DB (mock del repo o spy del service)
