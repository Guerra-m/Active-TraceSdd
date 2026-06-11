## ADDED Requirements

### Requirement: Crear convocatoria a coloquio
El sistema SHALL permitir crear una convocatoria con materia, fecha, cupo y descripción.

#### Scenario: Crear convocatoria exitosamente
- **WHEN** el usuario con permiso `coloquios:read` completa el formulario y confirma
- **THEN** el sistema llama a `POST /api/coloquios` y la convocatoria aparece en el listado

#### Scenario: Validación de cupo inválido
- **WHEN** el usuario ingresa cupo = 0 o negativo
- **THEN** el formulario muestra error de validación sin enviar

### Requirement: Importar alumnos a coloquio
El sistema SHALL permitir importar una lista de alumnos a una convocatoria.

#### Scenario: Importar alumnos
- **WHEN** el usuario selecciona alumnos del selector y confirma
- **THEN** el sistema llama a `POST /api/coloquios/{id}/alumnos` y los alumnos aparecen en la lista de la convocatoria

#### Scenario: Sin alumnos seleccionados
- **WHEN** el usuario intenta importar sin seleccionar ningún alumno
- **THEN** el sistema muestra validación de "seleccionar al menos un alumno"

### Requirement: Listado de convocatorias
El sistema SHALL mostrar el listado de convocatorias del tenant con estado y métricas básicas.

#### Scenario: Ver listado de convocatorias
- **WHEN** el usuario navega a `/coloquios`
- **THEN** el sistema muestra convocatorias con materia, fecha, cupo total, inscriptos y estado

### Requirement: Panel de métricas de coloquios
El sistema SHALL mostrar métricas agregadas de coloquios (aprobados, desaprobados, ausentes).

#### Scenario: Ver métricas
- **WHEN** el usuario navega a la vista de métricas de una convocatoria
- **THEN** el sistema muestra cantidad de aprobados, desaprobados, ausentes y nota promedio
