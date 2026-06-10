## Why

C-03 (auth-jwt-2fa) entregó autenticación completa: JWT verificado, `get_current_user` resuelve identidad y tenant desde el token. Sin embargo, **todos los endpoints autenticados aceptan cualquier usuario activo** — no existe control sobre qué acción puede ejecutar cada rol. El sistema necesita un modelo de autorización fino (`modulo:accion`) que sea administrable por datos, no por código, para habilitar el acceso diferenciado por los 7 roles del dominio desde el primer endpoint de negocio (C-05 en adelante).

## What Changes

- **Nuevas tablas de dominio**: `roles`, `permisos`, `rol_permiso` (catálogo administrable), `usuario_rol` (asignación de roles a usuarios con vigencia).
- **Migración Alembic 003**: crea las 4 tablas + seed de la matriz base de 7 roles × permisos del dominio desde `knowledge-base/03_actores_y_roles.md §3.3`.
- **Modelos ORM**: `Rol`, `Permiso`, `RolPermiso`, `UsuarioRol` con `TenantScopedBase` / `Base` según corresponda.
- **Servicio de resolución de permisos**: dada la sesión autenticada, calcula el conjunto de permisos efectivos del usuario (unión de roles activos y vigentes, acotados por tenant).
- **Dependency `require_permission("modulo:accion")`**: guard FastAPI que declara el permiso requerido por endpoint; fail-closed → 403 sin permiso explícito.
- **Slot reservado en `core/permissions.py` y `core/dependencies.py`** pasan a implementación real.
- **Catálogo administrable (CRUD básico)**: endpoints de lectura de roles y permisos para tenant ADMIN (sin interfaz aún — solo la API REST).

## Capabilities

### New Capabilities

- `rbac-catalog`: tablas `roles`, `permisos`, `rol_permiso` con CRUD administrable; seed de los 7 roles del dominio y su matriz de permisos base.
- `user-role-assignment`: tabla `usuario_rol` con vigencia temporal (`valid_from`, `valid_until`); asignación y revocación de roles a usuarios dentro del tenant.
- `permission-resolver`: lógica server-side que, dado un `User` autenticado, resuelve el conjunto de permisos efectivos (unión de roles vigentes, scope de tenant).
- `require-permission-guard`: dependency FastAPI `require_permission("modulo:accion")` que protege endpoints; fail-closed → 403.

### Modified Capabilities

- `app-scaffold`: se registran los nuevos routers de catálogo RBAC en el router principal de la API.

## Impact

- **Modelos**: 4 archivos nuevos en `backend/app/models/` (`rol.py`, `permiso.py`, `rol_permiso.py`, `usuario_rol.py`).
- **Repositories**: 4 nuevos en `backend/app/repositories/` para cada modelo.
- **Services**: `RbacService` con la lógica de resolución de permisos efectivos.
- **Routers**: `backend/app/api/v1/routers/rbac.py` — endpoints de catálogo (GET /roles, GET /permisos, GET /roles/{id}/permisos) con `require_permission`.
- **core/permissions.py**: implementación de `require_permission` (actualmente reservado).
- **core/dependencies.py**: integración del guard con `get_current_user`.
- **Alembic**: migración 003 + seed SQL en `alembic/versions/`.
- **Tests**: `tests/test_rbac.py` — usuario sin permiso → 403, unión de roles, permiso `(propio)` vs global, vigencia caducada, catálogo administrable.
- **Dependencias de código**: C-03 (User, get_current_user, JWT con `roles` claim); C-02 (TenantScopedBase, BaseRepository).
- **Desbloquea**: C-05 (audit-log), C-06 (estructura-academica), C-21 (frontend-shell-y-auth) — todos dependen de `require_permission` para proteger sus endpoints.
