## ADDED Requirements

### Requirement: Monitor general (F2.7)
El sistema SHALL mostrar al COORDINADOR/ADMIN un monitor general con métricas de estado del tenant.

#### Scenario: Ver monitor general
- **WHEN** el usuario con permiso `atrasados:ver` navega a `/monitor`
- **THEN** el sistema muestra métricas de alumnos atrasados, entregas pendientes y comunicaciones enviadas

#### Scenario: Sin permiso para monitor
- **WHEN** el usuario no tiene el permiso `atrasados:ver`
- **THEN** el sistema muestra el fallback de sin acceso

### Requirement: Seguimiento de coordinación con rango de fechas (F2.9)
El sistema SHALL permitir filtrar el monitor por rango de fechas para analizar períodos específicos.

#### Scenario: Filtrar por rango de fechas
- **WHEN** el usuario selecciona fecha_desde y fecha_hasta y aplica el filtro
- **THEN** el sistema llama a `GET /api/analisis/monitor?desde={fecha_desde}&hasta={fecha_hasta}` y actualiza las métricas

#### Scenario: Rango de fechas inválido
- **WHEN** el usuario selecciona fecha_hasta anterior a fecha_desde
- **THEN** el sistema muestra un error de validación y no envía la petición
