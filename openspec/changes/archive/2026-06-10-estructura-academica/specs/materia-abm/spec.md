## ADDED Requirements

### Requirement: Materia es catálogo plano del tenant con código único
El sistema SHALL mantener un catálogo de materias por tenant. Cada materia SHALL tener un `codigo` único dentro del tenant, un `nombre` y un `estado` (`Activa` o `Inactiva`). La materia NO está anidada dentro de una carrera — es el catálogo base sobre el cual se crearán instancias de dictado en changes posteriores. El borrado SHALL ser lógico.

#### Scenario: Crear materia con código único en el tenant
- **WHEN** un ADMIN hace POST `/api/v1/admin/materias` con `{"codigo": "MAT101", "nombre": "Matemática I"}`
- **THEN** el sistema retorna 201 con el objeto materia incluyendo `id`, `codigo`, `nombre`, `estado: "Activa"`, `tenant_id`

#### Scenario: Código duplicado en el mismo tenant retorna 409
- **WHEN** un ADMIN crea una materia con `codigo` que ya existe en el tenant
- **THEN** el sistema retorna 409 Conflict con `{"detail": "Código de materia ya existe en este tenant"}`

#### Scenario: El mismo código en otro tenant no causa conflicto
- **WHEN** dos tenants distintos crean materias con el mismo `codigo`
- **THEN** ambas operaciones son exitosas; el constraint es `(tenant_id, codigo)`

---

### Requirement: CRUD de materias restringido a ADMIN con permiso estructura:gestionar
El sistema SHALL proteger todos los endpoints `/api/v1/admin/materias` con `require_permission("estructura:gestionar")`. El listado SHALL filtrarse exclusivamente por el tenant del actor.

#### Scenario: ADMIN lista materias de su tenant
- **WHEN** un ADMIN hace GET `/api/v1/admin/materias`
- **THEN** el sistema retorna solo las materias (no borradas) de su tenant

#### Scenario: Aislamiento multi-tenant en materias
- **WHEN** dos ADMINs de tenants distintos listan materias simultáneamente
- **THEN** cada uno recibe solo las materias de su propio tenant

#### Scenario: Usuario sin permiso estructura:gestionar recibe 403
- **WHEN** un usuario ALUMNO intenta GET `/api/v1/admin/materias`
- **THEN** el sistema retorna 403 Forbidden

---

### Requirement: Cambio de estado de materia a Inactiva
El sistema SHALL permitir marcar una materia como `Inactiva` vía PATCH `/api/v1/admin/materias/{id}/estado`. Una materia `Inactiva` permanece en el catálogo (no se borra), pero futuros cambios podrán usarla como señal para restringir nuevos dictados.

#### Scenario: Cambiar estado a Inactiva
- **WHEN** un ADMIN hace PATCH `/api/v1/admin/materias/{id}/estado` con `{"estado": "Inactiva"}`
- **THEN** el sistema retorna 200 con la materia actualizada y `estado: "Inactiva"`

#### Scenario: Estado inválido retorna 422
- **WHEN** un ADMIN hace PATCH con `{"estado": "Suspendida"}` (valor no permitido)
- **THEN** el sistema retorna 422 Unprocessable Entity
