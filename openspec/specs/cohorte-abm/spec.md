## ADDED Requirements

### Requirement: Cohorte es una entidad temporal asociada a una carrera del tenant
El sistema SHALL mantener cohortes por tenant. Cada cohorte SHALL pertenecer a una `carrera_id` del mismo tenant. El nombre SHALL ser único dentro de `(tenant_id, carrera_id, nombre)`. Cada cohorte SHALL tener un `anio` (año académico), `vig_desde` (fecha de inicio) y `vig_hasta` opcional (fecha de cierre). El borrado SHALL ser lógico.

#### Scenario: Crear cohorte válida para carrera activa
- **WHEN** un ADMIN hace POST `/api/v1/admin/cohortes` con `{"carrera_id": "<uuid>", "nombre": "2024-A", "anio": 2024, "vig_desde": "2024-03-01"}`
- **THEN** el sistema retorna 201 con el objeto cohorte incluyendo `id`, `carrera_id`, `nombre`, `anio`, `vig_desde`, `vig_hasta: null`

#### Scenario: Nombre duplicado en la misma carrera del tenant retorna 409
- **WHEN** un ADMIN crea una cohorte con `nombre` que ya existe para la misma `carrera_id` en el mismo tenant
- **THEN** el sistema retorna 409 Conflict con `{"detail": "Nombre de cohorte ya existe para esta carrera en este tenant"}`

#### Scenario: Carrera de otro tenant no es accesible
- **WHEN** un ADMIN del tenant A intenta crear una cohorte con `carrera_id` que pertenece al tenant B
- **THEN** el sistema retorna 404 (la carrera no existe en el tenant del actor)

---

### Requirement: Creación de cohorte bloqueada si la carrera está inactiva
El sistema SHALL rechazar la creación de nuevas cohortes cuando la carrera asociada tiene `estado: "Inactiva"`. Las cohortes ya existentes no se ven afectadas por el cambio de estado de la carrera.

#### Scenario: Carrera inactiva bloquea nueva cohorte
- **WHEN** un ADMIN intenta crear una cohorte y la carrera referenciada tiene `estado: "Inactiva"`
- **THEN** el sistema retorna 422 con `{"detail": "No se pueden crear cohortes para una carrera inactiva"}`

#### Scenario: Cohorte existente de carrera inactiva sigue siendo visible
- **WHEN** una carrera se marca como `Inactiva` y ya tiene cohortes
- **THEN** GET `/api/v1/admin/cohortes` sigue retornando esas cohortes preexistentes

---

### Requirement: CRUD de cohortes restringido a ADMIN con permiso estructura:gestionar
El sistema SHALL proteger todos los endpoints `/api/v1/admin/cohortes` con `require_permission("estructura:gestionar")`. El listado SHALL filtrarse por tenant del actor.

#### Scenario: ADMIN lista cohortes de su tenant
- **WHEN** un ADMIN hace GET `/api/v1/admin/cohortes`
- **THEN** el sistema retorna solo las cohortes (no borradas) de su tenant

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario PROFESOR hace GET `/api/v1/admin/cohortes`
- **THEN** el sistema retorna 403 Forbidden
