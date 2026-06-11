## ADDED Requirements

### Requirement: Modificar vigencia de todas las asignaciones de un equipo
El sistema SHALL permitir actualizar las fechas `desde` y/o `hasta` de todas las asignaciones de un equipo (materia × carrera × cohorte) en una sola operación, vía `PATCH /api/v1/equipos/vigencia`. Requiere permiso `equipos:asignar`.

#### Scenario: Actualización exitosa de vigencias
- **WHEN** se envía `PATCH /api/v1/equipos/vigencia` con `materia_id`, `carrera_id`, `cohorte_id`, y al menos uno de `desde` o `hasta`
- **THEN** el sistema actualiza los campos indicados en todas las asignaciones no-eliminadas del equipo, retorna 200 con el conteo de filas actualizadas y emite audit `ASIGNACION_MODIFICAR` con `filas_afectadas=N`

#### Scenario: Sin asignaciones en el equipo
- **WHEN** el equipo especificado no tiene asignaciones activas
- **THEN** el sistema retorna 200 con `filas_actualizadas: 0`

#### Scenario: Payload sin campos de vigencia
- **WHEN** se envía el payload sin `desde` ni `hasta`
- **THEN** el sistema retorna 422 con mensaje "Debe especificar al menos desde o hasta"

#### Scenario: Equipo no pertenece al tenant
- **WHEN** alguno de los UUIDs (materia, carrera, cohorte) no existe en el tenant del actor
- **THEN** el sistema retorna 404

### Requirement: Solo se actualizan asignaciones no eliminadas
El sistema SHALL excluir las asignaciones con `deleted_at IS NOT NULL` de la actualización masiva de vigencia.

#### Scenario: Equipo con asignaciones eliminadas (soft-delete)
- **WHEN** el equipo tiene 4 asignaciones activas y 2 con soft-delete
- **THEN** solo las 4 activas se actualizan; las 2 eliminadas se ignoran
