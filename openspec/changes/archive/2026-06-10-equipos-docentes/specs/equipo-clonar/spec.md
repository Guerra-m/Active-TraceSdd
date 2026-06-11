## ADDED Requirements

### Requirement: Clonar equipo docente entre cohortes (RN-12)
El sistema SHALL permitir duplicar todas las asignaciones vigentes de un equipo origen (materia × carrera × cohorte) hacia un destino (misma materia × carrera × cohorte destino) con las fechas del nuevo período, vía `POST /api/v1/equipos/clonar`. Requiere permiso `equipos:asignar`.

#### Scenario: Clonado exitoso
- **WHEN** se envía `POST /api/v1/equipos/clonar` con `materia_id`, `carrera_id`, `cohorte_origen_id`, `cohorte_destino_id`, `desde` y `hasta` del nuevo período
- **THEN** el sistema duplica todas las asignaciones con `estado_vigencia == "Vigente"` del origen, crea nuevas asignaciones en el destino con las fechas del nuevo período, retorna 201 con la lista de asignaciones creadas y emite audit `ASIGNACION_MODIFICAR` con `filas_afectadas=N`

#### Scenario: Sin asignaciones vigentes en origen
- **WHEN** el equipo origen no tiene asignaciones vigentes
- **THEN** el sistema retorna 200 con lista vacía y mensaje "No hay asignaciones vigentes para clonar"

#### Scenario: Conflicto: asignación ya existe en destino
- **WHEN** en el destino ya existe una asignación no-eliminada para el mismo (usuario_id, rol, materia_id, cohorte_id, tenant_id)
- **THEN** el sistema omite ese registro en el clonado, crea el resto, y retorna 201 con la lista de creados más una lista de `conflictos` con los registros omitidos

#### Scenario: Cohorte destino igual a origen
- **WHEN** `cohorte_origen_id == cohorte_destino_id`
- **THEN** el sistema retorna 422 con mensaje "La cohorte destino debe ser distinta a la origen"

#### Scenario: Cohorte destino no pertenece al tenant
- **WHEN** `cohorte_destino_id` no existe en el tenant del actor
- **THEN** el sistema retorna 404

### Requirement: Las asignaciones vencidas NO se clonan
El sistema SHALL ignorar las asignaciones con `estado_vigencia == "Vencida"` al clonar; solo son histórico.

#### Scenario: Equipo con mezcla de vigentes y vencidas
- **WHEN** el equipo origen tiene 5 asignaciones vigentes y 3 vencidas
- **THEN** el sistema crea exactamente 5 asignaciones nuevas en el destino (las 3 vencidas se ignoran)
