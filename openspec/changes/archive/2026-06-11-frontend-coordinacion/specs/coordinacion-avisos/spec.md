## ADDED Requirements

### Requirement: Listado de avisos con filtro de vigencia
El sistema SHALL mostrar la lista de avisos institucionales con filtro por estado de vigencia (vigente/expirado/todos).

#### Scenario: Ver avisos vigentes
- **WHEN** el usuario con permiso `avisos:publicar` navega a `/avisos`
- **THEN** el sistema muestra por defecto los avisos vigentes con título, scope, fecha de publicación y estado

#### Scenario: Filtrar por estado
- **WHEN** el usuario cambia el filtro a "Expirados"
- **THEN** el listado se actualiza mostrando solo avisos con fecha de expiración pasada

### Requirement: Crear aviso con scope
El sistema SHALL permitir crear un aviso con scope Global, PorMateria, PorCohorte o PorRol.

#### Scenario: Crear aviso exitosamente
- **WHEN** el usuario completa el formulario con título, cuerpo, scope y fechas, y confirma
- **THEN** el sistema llama a `POST /api/avisos` y el nuevo aviso aparece en el listado

#### Scenario: Validación de campos requeridos
- **WHEN** el usuario envía el formulario sin título
- **THEN** el formulario muestra error de validación inline sin enviar la petición

### Requirement: Publicar aviso
El sistema SHALL permitir publicar un aviso en estado borrador.

#### Scenario: Publicar aviso
- **WHEN** el usuario hace clic en "Publicar" en un aviso en estado borrador
- **THEN** el sistema llama a `POST /api/avisos/{id}/publicar` y actualiza el estado en el listado

### Requirement: Confirmación de lectura (ack)
El sistema SHALL registrar la confirmación de lectura de un aviso por parte de un usuario.

#### Scenario: Confirmar lectura
- **WHEN** el usuario hace clic en "Confirmar lectura" en un aviso que lo requiere
- **THEN** el sistema llama a `POST /api/avisos/{id}/ack` y marca el aviso como leído

#### Scenario: Aviso ya leído
- **WHEN** el usuario ya confirmó lectura de un aviso
- **THEN** el botón "Confirmar lectura" está deshabilitado y muestra "Leído"

### Requirement: Editar y eliminar aviso
El sistema SHALL permitir editar un aviso existente o eliminarlo (soft delete).

#### Scenario: Editar aviso
- **WHEN** el usuario hace clic en "Editar" y modifica el aviso
- **THEN** el sistema llama a `PATCH /api/avisos/{id}` y refleja los cambios en el listado

#### Scenario: Eliminar aviso
- **WHEN** el usuario hace clic en "Eliminar" y confirma
- **THEN** el sistema llama a `DELETE /api/avisos/{id}` y el aviso desaparece del listado
