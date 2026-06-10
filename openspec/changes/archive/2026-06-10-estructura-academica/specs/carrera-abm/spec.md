## ADDED Requirements

### Requirement: Carrera es una entidad catálogo por tenant con unicidad de código
El sistema SHALL mantener un catálogo de carreras por tenant. Cada carrera SHALL tener un `codigo` único dentro del tenant y un `nombre` descriptivo. El estado SHALL ser `Activa` o `Inactiva`. El borrado SHALL ser lógico (soft delete), nunca físico.

#### Scenario: Crear carrera con código único en el tenant
- **WHEN** un ADMIN hace POST `/api/v1/admin/carreras` con `{"codigo": "ISI", "nombre": "Ingeniería en Sistemas"}`
- **THEN** el sistema retorna 201 con el objeto creado incluyendo `id`, `codigo`, `nombre`, `estado: "Activa"`, `tenant_id`

#### Scenario: Código duplicado en el mismo tenant retorna 409
- **WHEN** un ADMIN hace POST `/api/v1/admin/carreras` con un `codigo` que ya existe para ese tenant
- **THEN** el sistema retorna 409 Conflict con `{"detail": "Código de carrera ya existe en este tenant"}`

#### Scenario: El mismo código en otro tenant no causa conflicto
- **WHEN** dos tenants distintos crean carreras con el mismo `codigo`
- **THEN** ambas operaciones son exitosas; el constraint es `(tenant_id, codigo)` y no `codigo` global

---

### Requirement: CRUD de carreras restringido a ADMIN con permiso estructura:gestionar
El sistema SHALL proteger todos los endpoints `/api/v1/admin/carreras` con `require_permission("estructura:gestionar")`. Un usuario sin ese permiso SHALL recibir 403. La identidad del actor SHALL resolverse desde el JWT, nunca desde parámetros de la petición.

#### Scenario: ADMIN accede al listado de carreras
- **WHEN** un usuario con permiso `estructura:gestionar` hace GET `/api/v1/admin/carreras`
- **THEN** el sistema retorna 200 con la lista de carreras activas (no borradas) de su tenant

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario TUTOR hace GET `/api/v1/admin/carreras`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Listado aislado por tenant
- **WHEN** un ADMIN del tenant A lista carreras
- **THEN** el sistema retorna SOLO las carreras del tenant A, nunca de otros tenants

---

### Requirement: Cambio de estado de carrera controla apertura de cohortes
El sistema SHALL permitir cambiar el estado de una carrera a `Inactiva` vía PATCH `/api/v1/admin/carreras/{id}/estado`. Una carrera `Inactiva` SHALL impedir la creación de nuevas cohortes asociadas a ella. Las cohortes existentes NO se ven afectadas.

#### Scenario: Carrera activa puede recibir nuevas cohortes
- **WHEN** una carrera tiene `estado: "Activa"`
- **THEN** el endpoint POST `/api/v1/admin/cohortes` acepta nuevas cohortes para esa carrera

#### Scenario: Carrera inactiva bloquea creación de cohortes nuevas
- **WHEN** una carrera tiene `estado: "Inactiva"` y un ADMIN intenta crear una cohorte para ella
- **THEN** el sistema retorna 422 con `{"detail": "No se pueden crear cohortes para una carrera inactiva"}`

#### Scenario: Soft delete de carrera no expone el registro en listados
- **WHEN** un ADMIN hace DELETE `/api/v1/admin/carreras/{id}`
- **THEN** el sistema marca `deleted_at` con la fecha actual y el registro desaparece de futuros GET `/api/v1/admin/carreras`
