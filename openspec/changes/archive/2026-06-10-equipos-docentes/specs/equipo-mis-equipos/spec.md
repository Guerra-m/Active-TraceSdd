## ADDED Requirements

### Requirement: Docente puede ver sus propios equipos
El sistema SHALL retornar las asignaciones del usuario autenticado (resuelto del JWT) vía `GET /api/v1/equipos/mis-equipos`. La identidad NUNCA se acepta por parámetro.

#### Scenario: Docente con asignaciones activas
- **WHEN** un usuario autenticado llama `GET /api/v1/equipos/mis-equipos`
- **THEN** el sistema retorna las asignaciones cuyo `usuario_id` coincide con el `user_id` del JWT, incluyendo `estado_vigencia`, carrera, cohorte y materia de cada asignación

#### Scenario: Docente sin asignaciones
- **WHEN** el usuario autenticado no tiene asignaciones en el tenant
- **THEN** el sistema retorna una lista vacía `[]` con status 200

#### Scenario: Intento de ver equipos de otro usuario por parámetro
- **WHEN** se llama `GET /api/v1/equipos/mis-equipos` con cualquier query param de usuario_id
- **THEN** el sistema ignora el parámetro y retorna solo las asignaciones del JWT

### Requirement: Filtrado de mis equipos por estado y contexto
El sistema SHALL permitir filtrar los propios equipos por `estado_vigencia`, `materia_id`, `carrera_id` y `cohorte_id` via query params opcionales.

#### Scenario: Filtrar por vigencia activa
- **WHEN** se llama `GET /api/v1/equipos/mis-equipos?estado_vigencia=Vigente`
- **THEN** el sistema retorna solo las asignaciones con `estado_vigencia == "Vigente"`

#### Scenario: Filtrar por materia
- **WHEN** se llama con `materia_id=<uuid>`
- **THEN** el sistema retorna solo las asignaciones vinculadas a esa materia del tenant
