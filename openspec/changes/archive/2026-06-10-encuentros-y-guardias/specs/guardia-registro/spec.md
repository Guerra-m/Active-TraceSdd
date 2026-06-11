## ADDED Requirements

### Requirement: TUTOR registra una guardia propia (F6.6)
El sistema SHALL permitir `POST /api/v1/guardias` para crear un registro de guardia. El `asignacion_id` se resuelve del JWT (no del payload). Requiere `encuentros:gestionar`.

#### Scenario: Registro exitoso de guardia
- **WHEN** un TUTOR autenticado envía `POST /guardias` con `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `estado=Pendiente`
- **THEN** el sistema crea la guardia con `tenant_id` del JWT y retorna 201

#### Scenario: asignacion_id no viene del payload
- **WHEN** el payload incluye un `asignacion_id` externo
- **THEN** el sistema lo ignora y usa la primera asignación vigente del usuario autenticado para la materia indicada

### Requirement: Consulta de guardias con scope por rol (F6.6)
El sistema SHALL retornar `GET /api/v1/guardias`: si el actor tiene rol TUTOR (sin COORDINADOR/ADMIN), retorna solo sus propias guardias; si tiene COORDINADOR o ADMIN, retorna todas las del tenant. Filtros opcionales: `materia_id`, `estado`, `asignacion_id`.

#### Scenario: TUTOR ve solo sus guardias
- **WHEN** un TUTOR llama `GET /guardias` con guardias de otro tutor del mismo tenant
- **THEN** el sistema retorna solo las guardias del TUTOR autenticado

#### Scenario: COORDINADOR ve todas las guardias del tenant
- **WHEN** un COORDINADOR llama `GET /guardias`
- **THEN** el sistema retorna todas las guardias del tenant, incluyendo las de todos los tutores

### Requirement: Exportar guardias a CSV (F6.6)
El sistema SHALL retornar `GET /api/v1/guardias/exportar` como `StreamingResponse` CSV con columnas: id, asignacion_id, materia, carrera, cohorte, dia, horario, estado, comentarios. Requiere COORDINADOR o ADMIN (permiso `encuentros:gestionar`).

#### Scenario: Export CSV con datos
- **WHEN** un COORDINADOR llama `GET /guardias/exportar`
- **THEN** el sistema retorna `Content-Type: text/csv` con `Content-Disposition: attachment` y una fila por guardia del tenant no eliminada

#### Scenario: Export respeta tenant isolation
- **WHEN** hay guardias de dos tenants distintos
- **THEN** el CSV del tenant A contiene solo filas del tenant A
