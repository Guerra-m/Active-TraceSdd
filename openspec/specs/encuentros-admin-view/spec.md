## ADDED Requirements

### Requirement: Vista transversal de encuentros para coordinación (F6.5)
El sistema SHALL retornar `GET /api/v1/encuentros/admin` con todas las instancias del tenant sin restricción de creador, con filtros por `materia_id`, `estado`, `fecha_desde`, `fecha_hasta`. Requiere `encuentros:gestionar`.

#### Scenario: Admin ve encuentros de todos los docentes del tenant
- **WHEN** un COORDINADOR llama `GET /encuentros/admin` sin filtros
- **THEN** el sistema retorna todas las instancias del tenant (de todos los docentes/slots)

#### Scenario: Filtrar por estado no realizado
- **WHEN** se llama `GET /encuentros/admin?estado=Programado`
- **THEN** el sistema retorna solo instancias `Programado` del tenant completo

### Requirement: Vista admin respeta aislamiento de tenant
El sistema SHALL retornar únicamente instancias del tenant del JWT, aunque el usuario tenga rol ADMIN.

#### Scenario: Tenant isolation en admin view
- **WHEN** el tenant A hace `GET /encuentros/admin` y existen encuentros del tenant B
- **THEN** el sistema retorna solo los encuentros del tenant A
