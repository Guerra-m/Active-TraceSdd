## ADDED Requirements

### Requirement: Vista admin de encuentros
El sistema SHALL mostrar al ADMIN/COORDINADOR todos los encuentros del tenant con filtro por estado y período.

#### Scenario: Ver todos los encuentros
- **WHEN** el usuario con permiso `encuentros:gestionar` navega a `/encuentros/admin`
- **THEN** el sistema muestra todos los encuentros con alumno, tutor, fecha, tipo y estado

#### Scenario: Sin permiso de gestión
- **WHEN** el usuario no tiene `encuentros:gestionar`
- **THEN** el sistema muestra el fallback de sin acceso

### Requirement: Crear slots recurrentes de encuentro
El sistema SHALL permitir crear un slot recurrente (semanal/quincenal) para un período.

#### Scenario: Crear slot recurrente
- **WHEN** el usuario completa día_semana, hora, recurrencia y período, y confirma
- **THEN** el sistema llama a `POST /api/encuentros/slots-recurrentes` y los slots aparecen en el calendario

#### Scenario: Validación de slot sin día
- **WHEN** el usuario envía el formulario sin seleccionar día de la semana
- **THEN** el formulario muestra error de validación sin enviar

### Requirement: Editar instancia de encuentro
El sistema SHALL permitir editar la fecha, hora o estado de una instancia específica de encuentro.

#### Scenario: Editar instancia
- **WHEN** el usuario hace clic en "Editar" en un encuentro y modifica la fecha
- **THEN** el sistema llama a `PATCH /api/encuentros/{id}` y actualiza la instancia en el listado
