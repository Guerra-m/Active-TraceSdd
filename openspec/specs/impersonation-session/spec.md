## ADDED Requirements

### Requirement: Endpoint para iniciar sesión de impersonación
El sistema SHALL implementar `POST /api/v1/auth/impersonate` protegido con `require_permission("impersonacion:usar")`. El body recibe `{"user_id": UUID}` (el usuario a impersonar). Retorna un nuevo token de acceso con payload enriquecido: `{"sub": <impersonated_user_id>, "tenant_id": <tenant_id>, "actor_id": <real_actor_id>, "type": "access"}`. Registra `IMPERSONACION_INICIAR` en el audit log.

#### Scenario: ADMIN con permiso impersonacion:usar obtiene token de impersonación
- **WHEN** un usuario ADMIN hace `POST /api/v1/auth/impersonate` con `{"user_id": "<uuid_de_alumno>"}`
- **THEN** el sistema retorna 200 con un token de acceso cuyo payload contiene `sub = uuid_de_alumno`, `actor_id = uuid_de_admin` y `type = "access"`

#### Scenario: Usuario sin permiso impersonacion:usar recibe 403
- **WHEN** un usuario TUTOR (sin `impersonacion:usar`) hace `POST /api/v1/auth/impersonate`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Impersonación de usuario de otro tenant falla
- **WHEN** un ADMIN intenta impersonar a un usuario cuyo `tenant_id` difiere del token del actor
- **THEN** el sistema retorna 404 (el usuario no existe en el tenant del actor)

#### Scenario: Inicio de impersonación queda registrado en audit log
- **WHEN** se completa exitosamente `POST /api/v1/auth/impersonate`
- **THEN** existe un registro en `audit_log` con `accion = "IMPERSONACION_INICIAR"`, `actor_id` = ADMIN, `impersonado_id` = usuario impersonado

---

### Requirement: Endpoint para finalizar sesión de impersonación
El sistema SHALL implementar `DELETE /api/v1/auth/impersonate` que acepta el token de impersonación (Authorization header), registra `IMPERSONACION_FINALIZAR` en el audit log y retorna 204. No emite un nuevo token; el cliente debe usar su token original.

#### Scenario: Finalización registra IMPERSONACION_FINALIZAR
- **WHEN** el ADMIN hace `DELETE /api/v1/auth/impersonate` con el token de impersonación
- **THEN** el sistema retorna 204 y existe un registro en `audit_log` con `accion = "IMPERSONACION_FINALIZAR"`, `actor_id` = ADMIN, `impersonado_id` = usuario que se dejó de impersonar

#### Scenario: Token normal en DELETE /impersonate retorna 400
- **WHEN** se llama `DELETE /api/v1/auth/impersonate` con un token que no tiene `impersonated_id`
- **THEN** el sistema retorna 400 Bad Request con body `{"detail": "No hay sesión de impersonación activa"}`

---

### Requirement: get_current_user resuelve identidad efectiva bajo impersonación
El sistema SHALL modificar `get_current_user` para que, si el token contiene `impersonated_id`, retorne el usuario con id = `impersonated_id` (identidad efectiva). El `actor_id` del token real se almacena en `request.state.actor_id` para uso del helper de auditoría.

#### Scenario: Token de impersonación resuelve al usuario impersonado como current_user
- **WHEN** una petición llega con token que tiene `sub = uuid_alumno` y `actor_id = uuid_admin`
- **THEN** `get_current_user` retorna el objeto `User` con id = `uuid_alumno`

#### Scenario: request.state.actor_id contiene al actor real
- **WHEN** una petición llega con token de impersonación
- **THEN** `request.state.actor_id` es el UUID del ADMIN (actor real), no el UUID del alumno impersonado

#### Scenario: Token normal sin impersonated_id funciona igual que antes
- **WHEN** una petición llega con token sin campo `impersonated_id`
- **THEN** `get_current_user` retorna el usuario normal y `request.state.actor_id` es igual a `current_user.id`

---

### Requirement: Acciones bajo impersonación atribuidas al actor real en audit log
El sistema SHALL garantizar que cualquier llamada a `audit()` dentro de una sesión de impersonación use `actor_id = request.state.actor_id` (el actor real) e `impersonado_id = current_user.id` (el usuario impersonado). Esta atribución es responsabilidad del caller de `audit()`, no del helper.

#### Scenario: Acción del alumno impersonado se registra con actor real ADMIN
- **WHEN** un ADMIN impersona a un ALUMNO y ejecuta una acción que llama a `audit()` correctamente
- **THEN** el registro en `audit_log` tiene `actor_id = uuid_admin` e `impersonado_id = uuid_alumno`
