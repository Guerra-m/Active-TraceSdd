## ADDED Requirements

### Requirement: Listar alumnos atrasados
El sistema SHALL mostrar la lista de alumnos en estado de atraso para la comisión del profesor, consumiendo `GET /api/analisis/atrasados`.

#### Scenario: Ver atrasados con datos
- **WHEN** el profesor accede a `/profesor/atrasados`
- **THEN** el sistema muestra una tabla con nombre, legajo, cantidad de entregas atrasadas y fecha del último atraso

#### Scenario: Sin atrasados
- **WHEN** no hay alumnos atrasados en la comisión
- **THEN** el sistema muestra el mensaje "No hay alumnos atrasados en esta comisión"

### Requirement: Ver ranking de alumnos
El sistema SHALL mostrar un ranking de rendimiento de alumnos consumiendo `GET /api/analisis/ranking`.

#### Scenario: Ranking visible
- **WHEN** el profesor accede a la sección de ranking
- **THEN** el sistema muestra posición, nombre, legajo y promedio de cada alumno ordenados por promedio descendente

### Requirement: Ver notas finales
El sistema SHALL mostrar las notas finales de los alumnos de la comisión consumiendo `GET /api/analisis/notas-finales`.

#### Scenario: Notas finales disponibles
- **WHEN** el profesor accede a la sección de notas finales
- **THEN** el sistema muestra una tabla con nombre, legajo y nota final por alumno

#### Scenario: Error de carga
- **WHEN** el endpoint retorna un error
- **THEN** el sistema muestra un mensaje de error con botón para reintentar
