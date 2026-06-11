## ADDED Requirements

### Requirement: Monitor de seguimiento tutor/profesor
El sistema SHALL mostrar un panel unificado de seguimiento del estado de la comisión consumiendo `GET /api/analisis/monitor`.

#### Scenario: Monitor con datos
- **WHEN** el profesor accede a `/profesor/monitor`
- **THEN** el sistema muestra métricas de la comisión: total alumnos, atrasados, al día, promedio general y estado de comunicaciones

#### Scenario: Datos sin actividad
- **WHEN** la comisión no tiene actividad registrada
- **THEN** el sistema muestra los contadores en 0 sin errores

#### Scenario: Error de carga
- **WHEN** el endpoint retorna error
- **THEN** el sistema muestra un mensaje de error con botón para reintentar
