## MODIFIED Requirements

### Requirement: El guard expone el flag is_own_resource al endpoint
El sistema SHALL exponer en `request.state` tanto el flag `permission_is_own_resource` del permiso verificado **como** el `actor_id` del actor real de la sesión (que puede diferir de `current_user.id` bajo impersonación), permitiendo que el Service layer valide propiedad del recurso y que el helper de auditoría atribuya la acción correctamente sin volver a parsear el token.

#### Scenario: Endpoint recibe contexto de is_own_resource
- **WHEN** un usuario PROFESOR (is_own_resource=True) accede a un endpoint con `require_permission("calificaciones:importar")`
- **THEN** el `request.state` contiene `permission_is_own_resource=True` para que el Service valide que el recurso pertenece al usuario

#### Scenario: Usuario COORDINADOR tiene acceso global al mismo endpoint
- **WHEN** un usuario COORDINADOR (is_own_resource=False) accede al mismo endpoint
- **THEN** el `request.state` contiene `permission_is_own_resource=False` y el Service no restringe por propiedad

#### Scenario: Sesión normal expone actor_id igual a current_user.id
- **WHEN** una petición llega con token sin impersonación
- **THEN** `request.state.actor_id` es igual a `current_user.id`

#### Scenario: Sesión de impersonación expone actor_id del actor real
- **WHEN** una petición llega con token de impersonación (actor ADMIN, impersonado ALUMNO)
- **THEN** `request.state.actor_id` es el UUID del ADMIN y `current_user.id` es el UUID del ALUMNO
