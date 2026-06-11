## ADDED Requirements

### Requirement: Asignación masiva de docentes a un contexto
El sistema SHALL permitir asignar N usuarios en bloque a una combinación materia × carrera × cohorte × rol con una vigencia compartida, en una sola operación atómica (`POST /api/v1/equipos/masiva`). Requiere permiso `equipos:asignar`.

#### Scenario: Asignación masiva exitosa
- **WHEN** se envía `POST /api/v1/equipos/masiva` con lista de `usuario_ids` (1–200), `materia_id`, `carrera_id`, `cohorte_id`, `rol`, `desde` y `hasta` opcionales
- **THEN** el sistema crea una `Asignacion` por cada usuario, todos con el mismo contexto y vigencia, retorna 201 con la lista de asignaciones creadas y emite audit `ASIGNACION_MODIFICAR` con `filas_afectadas=N`

#### Scenario: Lista vacía de usuarios
- **WHEN** se envía `usuario_ids: []`
- **THEN** el sistema retorna 422 (validación Pydantic)

#### Scenario: Lista con más de 200 usuarios
- **WHEN** se envía `usuario_ids` con más de 200 elementos
- **THEN** el sistema retorna 422 con mensaje "Máximo 200 docentes por operación masiva"

#### Scenario: Usuario no pertenece al tenant
- **WHEN** uno de los `usuario_ids` no existe en el tenant del actor
- **THEN** la operación entera se rechaza con 404 y detalle del usuario no encontrado (sin crear ninguna asignación)

### Requirement: Autocompletado de docentes para asignación masiva
El sistema SHALL ofrecer `GET /api/v1/equipos/buscar-docentes?q=<término>` para búsqueda por nombre/apellido con máximo 50 resultados. Requiere permiso `equipos:asignar`.

#### Scenario: Búsqueda con término de 2+ caracteres
- **WHEN** se llama con `q=mar` (2 o más caracteres)
- **THEN** el sistema retorna usuarios del tenant cuyo nombre o apellido contiene "mar" (case-insensitive), máx 50 resultados, solo usuarios no eliminados

#### Scenario: Búsqueda con término menor a 2 caracteres
- **WHEN** se llama con `q=m` (1 carácter)
- **THEN** el sistema retorna 422 con mensaje "El término de búsqueda debe tener al menos 2 caracteres"

#### Scenario: Sin resultados
- **WHEN** el término no coincide con ningún usuario
- **THEN** el sistema retorna lista vacía `[]` con status 200
