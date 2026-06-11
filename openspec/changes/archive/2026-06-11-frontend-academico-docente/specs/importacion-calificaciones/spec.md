## ADDED Requirements

### Requirement: Preview de actividades antes de importar
El sistema SHALL mostrar un listado de actividades disponibles en Moodle antes de confirmar la importación, obtenido de `GET /api/calificaciones/preview?comision_id=<id>`.

#### Scenario: Cargar preview exitoso
- **WHEN** el profesor navega a `/profesor/importar` con una comisión seleccionada
- **THEN** el sistema muestra una tabla con las actividades disponibles y checkboxes para seleccionar

#### Scenario: Sin actividades disponibles
- **WHEN** el preview retorna una lista vacía
- **THEN** el sistema muestra el mensaje "No hay actividades disponibles para importar"

### Requirement: Selección y confirmación de importación
El sistema SHALL permitir al profesor seleccionar actividades específicas y confirmar la importación con `POST /api/calificaciones/import`.

#### Scenario: Importación exitosa
- **WHEN** el profesor selecciona al menos una actividad y confirma
- **THEN** el sistema llama al endpoint, muestra feedback de éxito y limpia la selección

#### Scenario: Importación sin selección
- **WHEN** el profesor intenta confirmar sin seleccionar ninguna actividad
- **THEN** el sistema muestra el error "Seleccioná al menos una actividad" y bloquea el submit

#### Scenario: Error de red en importación
- **WHEN** el endpoint retorna un error HTTP
- **THEN** el sistema muestra el mensaje de error del servidor y permite reintentar
