## ADDED Requirements

### Requirement: Ver entregas pendientes de corrección
El sistema SHALL mostrar las entregas sin corregir de la comisión consumiendo `GET /api/analisis/entregas-sin-corregir`.

#### Scenario: Entregas pendientes con datos
- **WHEN** el profesor accede a `/profesor/entregas`
- **THEN** el sistema muestra una tabla con alumno, actividad, fecha de entrega y estado

#### Scenario: Sin entregas pendientes
- **WHEN** no hay entregas sin corregir
- **THEN** el sistema muestra el mensaje "No hay entregas pendientes de corrección"

### Requirement: Exportar entregas a CSV
El sistema SHALL permitir exportar la lista de entregas sin corregir en formato CSV.

#### Scenario: Export exitoso
- **WHEN** el profesor hace clic en "Exportar CSV"
- **THEN** el navegador descarga un archivo CSV con todos los datos de la tabla

#### Scenario: Export con lista vacía
- **WHEN** no hay entregas y el profesor intenta exportar
- **THEN** el botón de export está deshabilitado
