## ADDED Requirements

### Requirement: Listado de equipos docentes
El sistema SHALL mostrar al COORDINADOR/ADMIN la lista de equipos docentes del tenant con nombre, período de vigencia y cantidad de tutores asignados.

#### Scenario: Ver listado de equipos
- **WHEN** el usuario con permiso `equipos:asignar` navega a `/equipos`
- **THEN** el sistema muestra la lista de equipos con nombre, período, tutores y acciones

#### Scenario: Acceso denegado sin permiso
- **WHEN** el usuario no tiene el permiso `equipos:asignar`
- **THEN** el sistema muestra el mensaje de sin acceso en lugar del contenido

### Requirement: Asignación masiva de tutores
El sistema SHALL permitir asignar un tutor a múltiples alumnos/comisiones en una sola operación.

#### Scenario: Asignación masiva exitosa
- **WHEN** el usuario selecciona alumnos/comisiones y elige un tutor, luego confirma
- **THEN** el sistema llama a `POST /api/equipos/{id}/asignacion-masiva` y muestra confirmación de éxito

#### Scenario: Error en asignación masiva
- **WHEN** la API retorna un error
- **THEN** el sistema muestra el mensaje de error sin navegar fuera

### Requirement: Clonar equipo entre períodos
El sistema SHALL permitir clonar un equipo existente para un nuevo período.

#### Scenario: Clonar equipo exitosamente
- **WHEN** el usuario selecciona "Clonar" en un equipo y elige el período destino
- **THEN** el sistema llama a `POST /api/equipos/{id}/clonar` y navega al nuevo equipo creado

#### Scenario: Clonar con período inválido
- **WHEN** el usuario intenta clonar sin seleccionar período destino
- **THEN** el formulario muestra un error de validación antes de enviar

### Requirement: Modificar vigencia en bloque
El sistema SHALL permitir modificar el rango de vigencia de múltiples equipos seleccionados.

#### Scenario: Modificar vigencia en bloque
- **WHEN** el usuario selecciona varios equipos y elige "Modificar vigencia"
- **THEN** el sistema muestra un formulario con fecha_inicio y fecha_fin, y al confirmar llama `PATCH /api/equipos/vigencia-bulk`

### Requirement: Exportar lista de equipos
El sistema SHALL permitir exportar la lista de equipos en formato CSV.

#### Scenario: Exportar equipos
- **WHEN** el usuario hace clic en "Exportar"
- **THEN** el sistema dispara la descarga de un archivo CSV con los datos del listado
