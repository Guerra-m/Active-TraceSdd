## ADDED Requirements

### Requirement: Generar bloque HTML para el aula virtual (F6.4)
El sistema SHALL retornar `GET /api/v1/encuentros/aula-virtual` con `Content-Type: text/html`, un bloque `<ul>` con una `<li>` por cada instancia no cancelada de la materia/asignación filtrada, ordenadas por fecha ascendente.

#### Scenario: Bloque HTML con instancias programadas y realizadas
- **WHEN** se llama `GET /encuentros/aula-virtual?materia_id=<uuid>` con instancias en estado Programado y Realizado
- **THEN** el sistema retorna HTML con `Content-Type: text/html`, un `<ul>` con items que incluyen fecha, hora, título y `<a href>` para meet_url y video_url (si existe)

#### Scenario: Sin instancias disponibles
- **WHEN** no hay instancias no canceladas para los filtros dados
- **THEN** el sistema retorna HTML con `<ul></ul>` vacío (200)

#### Scenario: Instancias canceladas excluidas del bloque
- **WHEN** hay una mezcla de instancias Programado, Realizado y Cancelado
- **THEN** el bloque HTML NO incluye las instancias con estado `Cancelado`

### Requirement: Orden cronológico ascendente en el bloque HTML
El sistema SHALL ordenar las instancias en el bloque HTML por `fecha` ASC y dentro de la misma fecha por `hora` ASC.

#### Scenario: Múltiples instancias en diferentes fechas
- **WHEN** hay instancias en 2024-03-04, 2024-03-18 y 2024-03-11
- **THEN** el HTML las presenta en orden 2024-03-04, 2024-03-11, 2024-03-18
