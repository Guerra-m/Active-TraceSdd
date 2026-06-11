## ADDED Requirements

### Requirement: Listado de tareas propias
El sistema SHALL mostrar al usuario sus tareas asignadas con estado y fecha límite.

#### Scenario: Ver mis tareas
- **WHEN** el usuario con permiso `tareas:gestionar` navega a `/tareas`
- **THEN** el sistema muestra las tareas asignadas al usuario con título, estado, asignado_a y fecha_limite

#### Scenario: Sin tareas asignadas
- **WHEN** el usuario no tiene tareas asignadas
- **THEN** el sistema muestra un mensaje "No hay tareas asignadas"

### Requirement: Crear y asignar tarea
El sistema SHALL permitir crear una tarea y asignarla a un usuario del tenant.

#### Scenario: Crear tarea exitosamente
- **WHEN** el usuario completa título, descripción, asignado_a y fecha_límite, y confirma
- **THEN** el sistema llama a `POST /api/tareas` y la tarea aparece en el listado

#### Scenario: Validación de tarea sin asignado
- **WHEN** el usuario envía el formulario sin seleccionar un asignado
- **THEN** el formulario muestra error de validación sin enviar la petición

### Requirement: Delegar tarea
El sistema SHALL permitir reasignar una tarea a otro usuario.

#### Scenario: Delegar tarea
- **WHEN** el usuario hace clic en "Delegar" y selecciona otro usuario
- **THEN** el sistema llama a `PATCH /api/tareas/{id}/delegar` y actualiza el campo asignado_a

### Requirement: Cambiar estado de tarea
El sistema SHALL permitir cambiar el estado de una tarea (Pendiente → En progreso → Completada → Cancelada).

#### Scenario: Cambiar estado exitosamente
- **WHEN** el usuario selecciona un nuevo estado en el selector
- **THEN** el sistema llama a `PATCH /api/tareas/{id}/estado` y actualiza el estado en la UI

#### Scenario: Estado inválido rechazado
- **WHEN** el usuario intenta una transición no permitida
- **THEN** la API retorna 400 y el sistema muestra el error sin cambiar el estado

### Requirement: Agregar comentario a tarea
El sistema SHALL permitir agregar comentarios a una tarea para comunicación asincrónica.

#### Scenario: Agregar comentario
- **WHEN** el usuario escribe un comentario y hace clic en "Enviar"
- **THEN** el sistema llama a `POST /api/tareas/{id}/comentarios` y el comentario aparece en la lista
