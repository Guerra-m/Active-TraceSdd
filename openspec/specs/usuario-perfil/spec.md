## ADDED Requirements

### Requirement: Usuario extiende el modelo de auth con perfil PII cifrado
El sistema SHALL extender la tabla `users` con campos de perfil docente. Los campos PII (`dni`, `cuil`, `cbu`, `alias_cbu`) SHALL almacenarse cifrados con AES-256 en reposo. El email ya está cifrado desde C-02 y no se duplica. Los campos SHALL estar disponibles vía ABM restringido a ADMIN con permiso `usuarios:gestionar`.

#### Scenario: Crear usuario con perfil completo retorna 201
- **WHEN** un ADMIN hace POST `/api/v1/admin/usuarios` con nombre, apellidos, email, dni, cuil, banco, cbu, alias_cbu, regional, legajo, facturador
- **THEN** el sistema retorna 201 con el objeto creado; PII (`dni`, `cuil`, `cbu`, `alias_cbu`) NOT incluida en la respuesta

#### Scenario: PII no aparece en texto plano en la base de datos
- **WHEN** se consulta directamente la tabla `users` en la DB de test
- **THEN** las columnas `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted` contienen valores cifrados, nunca texto plano

#### Scenario: Email único por tenant
- **WHEN** un ADMIN intenta crear un segundo usuario con el mismo email en el mismo tenant
- **THEN** el sistema retorna 409 Conflict con mensaje de email duplicado

#### Scenario: El mismo email en otro tenant no causa conflicto
- **WHEN** dos tenants distintos crean usuarios con el mismo email
- **THEN** ambas operaciones son exitosas; el constraint es `(tenant_id, email_hash)` y no `email_hash` global

#### Scenario: Respuesta estándar no expone PII sensible
- **WHEN** un ADMIN hace GET `/api/v1/admin/usuarios/{id}`
- **THEN** la respuesta incluye nombre, apellidos, banco, regional, legajo, estado, pero NO incluye dni, cuil, cbu, alias_cbu

---

### Requirement: ABM de usuarios restringido a ADMIN con permiso usuarios:gestionar
El sistema SHALL proteger todos los endpoints `/api/v1/admin/usuarios` con `require_permission("usuarios:gestionar")`. La identidad del actor SHALL resolverse desde el JWT; el `tenant_id` SHALL filtrarse desde el token, nunca desde parámetros de la petición.

#### Scenario: ADMIN lista usuarios de su tenant
- **WHEN** un ADMIN hace GET `/api/v1/admin/usuarios`
- **THEN** el sistema retorna solo los usuarios (no borrados) del tenant del ADMIN

#### Scenario: COORDINADOR sin permiso usuarios:gestionar recibe 403
- **WHEN** un COORDINADOR hace GET `/api/v1/admin/usuarios`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Aislamiento multi-tenant en usuarios
- **WHEN** un ADMIN del tenant A lista usuarios
- **THEN** no aparece ningún usuario del tenant B

---

### Requirement: Soft delete de usuario preserva historial
El sistema SHALL implementar DELETE como soft delete (poblar `deleted_at`). Un usuario soft-deleted SHALL seguir siendo referenciado por AuditLog y Asignacion pero no SHALL aparecer en listados activos.

#### Scenario: Soft delete oculta al usuario del listado
- **WHEN** un ADMIN hace DELETE `/api/v1/admin/usuarios/{id}`
- **THEN** el sistema retorna 204 y el usuario desaparece de GET `/api/v1/admin/usuarios`

#### Scenario: Asignaciones del usuario soft-deleted permanecen en histórico
- **WHEN** un usuario con asignaciones activas es soft-deleted
- **THEN** las asignaciones existen en DB (su deleted_at no se puebla automáticamente)
