## ADDED Requirements

### Requirement: Guard require_permission fail-closed
El sistema SHALL implementar `require_permission(code: str)` como una factory que retorna una dependency FastAPI. La dependency verifica que el usuario autenticado (resuelto por `get_current_user`) tiene el permiso con el `code` indicado en su set de permisos efectivos. Si el permiso no está presente → 403 Forbidden inmediato. Sin permiso explícito, el acceso SIEMPRE se deniega.

#### Scenario: Usuario con permiso correcto accede al endpoint
- **WHEN** un usuario con permiso `calificaciones:importar` hace una petición a un endpoint protegido con `require_permission("calificaciones:importar")`
- **THEN** el sistema procesa la petición normalmente (no lanza excepción)

#### Scenario: Usuario sin el permiso recibe 403
- **WHEN** un usuario sin permiso `calificaciones:importar` hace una petición a un endpoint protegido con `require_permission("calificaciones:importar")`
- **THEN** el sistema retorna 403 Forbidden con body `{"detail": "Permiso insuficiente: calificaciones:importar"}`

#### Scenario: Usuario no autenticado recibe 401 antes del check de permiso
- **WHEN** una petición llega sin header Authorization al endpoint protegido
- **THEN** el sistema retorna 401 Unauthorized (el guard de autenticación de `get_current_user` actúa primero)

#### Scenario: Rol con asignación vencida no otorga acceso
- **WHEN** un usuario tenía el permiso requerido pero su asignación de rol expiró (valid_until en el pasado)
- **THEN** el sistema retorna 403 Forbidden

---

### Requirement: El guard expone el flag is_own_resource al endpoint
El sistema SHALL exponer en `request.state` tanto el flag `permission_is_own_resource` del permiso verificado **como** el `actor_id` del actor real de la sesión (que puede diferir de `current_user.id` bajo impersonación), permitiendo que el Service layer valide propiedad del recurso y que el helper de auditoría atribuya la acción correctamente sin volver a parsear el token.

#### Scenario: Endpoint recibe contexto de is_own_resource
- **WHEN** un usuario PROFESOR (is_own_resource=True) accede a un endpoint con `require_permission("calificaciones:importar")`
- **THEN** el request.state contiene `permission_is_own_resource=True` para que el Service valide que el recurso pertenece al usuario

#### Scenario: Usuario COORDINADOR tiene acceso global al mismo endpoint
- **WHEN** un usuario COORDINADOR (is_own_resource=False) accede al mismo endpoint
- **THEN** el request.state contiene `permission_is_own_resource=False` y el Service no restringe por propiedad

#### Scenario: Sesión normal expone actor_id igual a current_user.id
- **WHEN** una petición llega con token sin impersonación
- **THEN** `request.state.actor_id` es igual a `current_user.id`

#### Scenario: Sesión de impersonación expone actor_id del actor real
- **WHEN** una petición llega con token de impersonación (actor ADMIN, impersonado ALUMNO)
- **THEN** `request.state.actor_id` es el UUID del ADMIN y `current_user.id` es el UUID del ALUMNO

---

### Requirement: Declaración explícita de permiso por endpoint
El sistema SHALL requerir que cada endpoint protegido declare explícitamente su permiso requerido via `Depends(require_permission("modulo:accion"))`. No existe permiso por defecto ni acceso implícito. Todo endpoint sin `require_permission` explícito que requiera usuario autenticado usa solo `get_current_user` (autenticado pero sin verificación de permiso extra).

#### Scenario: Endpoint sin require_permission acepta cualquier usuario autenticado
- **WHEN** un endpoint usa solo `Depends(get_current_user)` sin `require_permission`
- **THEN** cualquier usuario autenticado puede acceder (solo se verifica autenticación, no permisos específicos)

#### Scenario: Endpoint con require_permission incorrecto falla en startup
- **WHEN** se define `require_permission("modulo_inexistente:accion")` y el código de permiso no existe en DB
- **THEN** la validación en tiempo de ejecución retorna 403 (permiso no encontrado en el set del usuario)
