## ADDED Requirements

### Requirement: Asignacion vincula usuario con rol académico y vigencia temporal
El sistema SHALL implementar `Asignacion` como la entidad que relaciona un `usuario_id` con un `rol` (PROFESOR|TUTOR|COORDINADOR|NEXO|ADMIN|FINANZAS), un contexto académico opcional (`materia_id`, `carrera_id`, `cohorte_id`), `comisiones` (lista de strings, JSONB), `responsable_id` (FK → Usuario nullable), vigencia `desde/hasta`. El campo `estado_vigencia` SHALL ser derivado en runtime: "Vigente" si `hoy >= desde AND (hasta IS NULL OR hoy <= hasta)`, "Vencida" en otro caso. El borrado SHALL ser lógico.

#### Scenario: Crear asignación válida retorna 201 con estado_vigencia Vigente
- **WHEN** un ADMIN crea una asignación con `desde=hoy`, `hasta=null` para un usuario y materia del mismo tenant
- **THEN** el sistema retorna 201 con `estado_vigencia: "Vigente"`

#### Scenario: Asignación vencida tiene estado_vigencia Vencida
- **WHEN** se consulta una asignación cuya `hasta` es una fecha anterior a hoy
- **THEN** la respuesta incluye `estado_vigencia: "Vencida"`

#### Scenario: Usuario con contexto de otro tenant da 404
- **WHEN** un ADMIN del tenant A intenta crear asignación con `materia_id` del tenant B
- **THEN** el sistema retorna 404 (la materia no existe en el tenant del actor)

---

### Requirement: Asignación vencida no otorga permisos pero se conserva en histórico
El sistema SHALL conservar todas las asignaciones vencidas como registro histórico. Una asignación con `hasta < hoy` NO SHALL usarse para resolver permisos RBAC del usuario. La consulta de asignaciones SHALL retornar tanto vigentes como vencidas; el filtrado SHALL ser responsabilidad del llamador.

#### Scenario: Asignación vencida permanece en listado
- **WHEN** un ADMIN lista todas las asignaciones de un tenant
- **THEN** aparecen tanto vigentes como vencidas, con `estado_vigencia` indicado

#### Scenario: Asignación vencida no se incluye en resolución de permisos
- **WHEN** un usuario intenta acceder a un endpoint protegido con un permiso que solo tendría por una asignación vencida
- **THEN** el sistema retorna 403 (el RBAC de C-04 ya filtra por valid_until en UsuarioRol)

---

### Requirement: CRUD de asignaciones restringido con permiso equipos:asignar
El sistema SHALL proteger todos los endpoints `/api/v1/asignaciones` con `require_permission("equipos:asignar")`. El listado SHALL soportar filtros opcionales: `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`.

#### Scenario: COORDINADOR lista asignaciones con filtro por materia
- **WHEN** un COORDINADOR hace GET `/api/v1/asignaciones?materia_id=<uuid>`
- **THEN** el sistema retorna solo las asignaciones (no borradas) de esa materia dentro del tenant

#### Scenario: Usuario sin permiso equipos:asignar recibe 403
- **WHEN** un PROFESOR hace GET `/api/v1/asignaciones`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Aislamiento multi-tenant en asignaciones
- **WHEN** un ADMIN del tenant A lista asignaciones
- **THEN** no aparece ninguna asignación del tenant B

---

### Requirement: Jerarquía docente via responsable_id
El sistema SHALL permitir establecer un `responsable_id` en cada asignación para modelar la jerarquía "a quién rinde cuentas este docente en este contexto". `responsable_id` SHALL ser nullable y SHALL ser un `usuario_id` válido del mismo tenant.

#### Scenario: responsable_id de otro tenant da 404
- **WHEN** se intenta crear una asignación con `responsable_id` de un usuario de otro tenant
- **THEN** el sistema retorna 404 (el usuario responsable no existe en el tenant del actor)

#### Scenario: responsable_id null es válido
- **WHEN** se crea una asignación sin `responsable_id`
- **THEN** el sistema crea la asignación exitosamente con `responsable_id: null`
