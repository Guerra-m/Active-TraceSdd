## ADDED Requirements

### Requirement: Exportar equipo a CSV descargable
El sistema SHALL generar un archivo CSV descargable con el detalle de todas las asignaciones de un equipo filtrado, vía `GET /api/v1/equipos/exportar`. Requiere permiso `equipos:asignar`.

#### Scenario: Export exitoso con datos
- **WHEN** se llama `GET /api/v1/equipos/exportar` con filtros opcionales (materia_id, carrera_id, cohorte_id, rol, estado_vigencia)
- **THEN** el sistema retorna un `StreamingResponse` con `Content-Type: text/csv` y `Content-Disposition: attachment; filename="equipo_<timestamp>.csv"`, con una fila de encabezado y una fila por asignación del tenant que cumple los filtros

#### Scenario: Columnas del CSV
- **WHEN** se descarga el CSV
- **THEN** el archivo contiene exactamente las columnas: `id`, `usuario_email`, `rol`, `materia_codigo`, `carrera_codigo`, `cohorte_nombre`, `comisiones`, `responsable_email`, `desde`, `hasta`, `estado_vigencia`

#### Scenario: Email desencriptado en el CSV
- **WHEN** el CSV incluye filas con email cifrado
- **THEN** el valor de `usuario_email` está desencriptado (AES-256 decrypt) — nunca el blob cifrado

#### Scenario: Sin asignaciones que cumplan los filtros
- **WHEN** no hay asignaciones que cumplan los filtros aplicados
- **THEN** el sistema retorna un CSV con solo la fila de encabezado (sin filas de datos)

### Requirement: El export respeta el scope de tenant
El sistema SHALL incluir en el CSV únicamente asignaciones del tenant del actor autenticado; ninguna fila de otros tenants puede aparecer en el export.

#### Scenario: Tenant isolation en export
- **WHEN** el tenant A solicita el export y existe el tenant B con asignaciones similares
- **THEN** el CSV del tenant A solo contiene asignaciones cuyo `tenant_id` coincide con el tenant del JWT
