## ADDED Requirements

### Requirement: Crear slot recurrente genera N instancias automáticamente (RN-13)
El sistema SHALL aceptar `POST /api/v1/encuentros/slots` con modo `recurrente` (dia_semana + fecha_inicio + cant_semanas) y crear automáticamente N `InstanciaEncuentro` con estado `Programado`, una por semana desde `fecha_inicio`. Requiere `encuentros:gestionar`.

#### Scenario: Slot recurrente de 4 semanas
- **WHEN** se envía `POST /encuentros/slots` con `cant_semanas=4`, `fecha_inicio=2024-03-04`, `hora=18:00`, `titulo="Clase 1"`
- **THEN** el sistema crea 1 `SlotEncuentro` y 4 `InstanciaEncuentro` con fechas 2024-03-04, 2024-03-11, 2024-03-18, 2024-03-25, todas con estado `Programado`, retorna 201 con el slot y la lista de instancias creadas

#### Scenario: cant_semanas mayor a 52 rechazado
- **WHEN** se envía `cant_semanas=53`
- **THEN** el sistema retorna 422 con mensaje "Máximo 52 semanas"

### Requirement: Crear encuentro único genera 1 instancia (RN-13)
El sistema SHALL aceptar `POST /api/v1/encuentros/slots` con modo `unico` (fecha_unica + hora) y crear directamente 1 `InstanciaEncuentro` con `slot_id=NULL`. No se crea ningún `SlotEncuentro`.

#### Scenario: Encuentro único
- **WHEN** se envía `POST /encuentros/slots` con `fecha_unica=2024-03-15`, `hora=10:00`, `titulo="Clase extraordinaria"`
- **THEN** el sistema crea 1 `InstanciaEncuentro` con `slot_id=NULL` y estado `Programado`, retorna 201

#### Scenario: Payload con ambos modos (recurrente y único)
- **WHEN** se envía un payload con `cant_semanas > 0` Y `fecha_unica` ambos presentes
- **THEN** el sistema retorna 422 indicando que los modos son excluyentes

### Requirement: Listado de slots del tenant con filtros
El sistema SHALL retornar `GET /api/v1/encuentros/slots` con filtros opcionales por `materia_id` y `asignacion_id`. Solo slots no eliminados del tenant del actor.

#### Scenario: Listar slots con filtro por materia
- **WHEN** se llama `GET /encuentros/slots?materia_id=<uuid>`
- **THEN** el sistema retorna solo los slots de esa materia del tenant, con la lista de instancias asociadas
