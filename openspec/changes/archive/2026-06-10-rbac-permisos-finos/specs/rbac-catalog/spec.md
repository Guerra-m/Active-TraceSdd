## ADDED Requirements

### Requirement: Catálogo de roles persistente
El sistema SHALL mantener una tabla `roles` con los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) más soporte para roles custom por tenant. Cada rol tiene `code` (único), `name`, `is_system` (roles del dominio = `True`, no modificables), `tenant_id` (NULL para roles del sistema), `is_active`, `created_at`, `updated_at`, `deleted_at` (soft delete).

#### Scenario: Roles del dominio existen tras la migración
- **WHEN** se aplica la migración 003
- **THEN** la tabla `roles` contiene exactamente 7 filas con `is_system=True` y `tenant_id=NULL` para los roles ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS

#### Scenario: Rol custom por tenant puede crearse
- **WHEN** un usuario con permiso `roles:crear` crea un rol con `tenant_id` explícito
- **THEN** el rol se persiste con `is_system=False` y está disponible solo para ese tenant

#### Scenario: Rol del sistema no puede eliminarse
- **WHEN** se intenta soft-delete de un rol con `is_system=True`
- **THEN** el sistema retorna 409 Conflict con mensaje "No se puede eliminar un rol del sistema"

---

### Requirement: Catálogo de permisos persistente
El sistema SHALL mantener una tabla `permisos` con todos los permisos del dominio en formato `modulo:accion`. Cada permiso tiene `code` (único, formato `modulo:accion`), `description`, `is_active`, `created_at`.

#### Scenario: Permisos del dominio existen tras la migración
- **WHEN** se aplica la migración 003
- **THEN** la tabla `permisos` contiene al menos los siguientes permisos: `academico:ver_propio`, `evaluacion:reservar`, `avisos:confirmar`, `calificaciones:importar`, `atrasados:ver`, `entregas:ver`, `comunicacion:enviar`, `comunicacion:aprobar`, `encuentros:gestionar`, `guardias:registrar`, `tareas:gestionar`, `avisos:publicar`, `equipos:asignar`, `estructura:gestionar`, `usuarios:gestionar`, `auditoria:ver`, `liquidaciones:operar`, `liquidaciones:cerrar`, `facturas:gestionar`, `tenant:configurar`, `impersonacion:usar`

#### Scenario: Código de permiso respeta formato modulo:accion
- **WHEN** se intenta crear un permiso con `code` que no contiene exactamente un `:` separando módulo y acción
- **THEN** el sistema retorna 422 Unprocessable Entity

---

### Requirement: Matriz rol-permiso administrable
El sistema SHALL mantener una tabla `rol_permiso` que asocia roles con permisos. Cada fila tiene `rol_id`, `permiso_id`, `tenant_id`, `is_own_resource` (bool, default False), `created_at`. La combinación `(rol_id, permiso_id, tenant_id)` es UNIQUE.

#### Scenario: Seed de la matriz base tras la migración
- **WHEN** se aplica la migración 003
- **THEN** la tabla `rol_permiso` refleja la matriz de `knowledge-base/03_actores_y_roles.md §3.3`: PROFESOR tiene `calificaciones:importar` con `is_own_resource=True`; COORDINADOR tiene `calificaciones:importar` con `is_own_resource=False`

#### Scenario: Consulta de permisos de un rol
- **WHEN** se hace GET `/api/v1/rbac/roles/{rol_id}/permisos` con un usuario autenticado con permiso `roles:ver`
- **THEN** el sistema retorna la lista de permisos del rol con su flag `is_own_resource`

---

### Requirement: Endpoints GET del catálogo
El sistema SHALL exponer endpoints de lectura del catálogo RBAC protegidos con `require_permission`.

#### Scenario: Listar roles disponibles
- **WHEN** un usuario con permiso `roles:ver` hace GET `/api/v1/rbac/roles`
- **THEN** el sistema retorna la lista de roles activos (sistema + custom del tenant del usuario)

#### Scenario: Acceso denegado sin permiso
- **WHEN** un usuario sin permiso `roles:ver` hace GET `/api/v1/rbac/roles`
- **THEN** el sistema retorna 403 Forbidden
