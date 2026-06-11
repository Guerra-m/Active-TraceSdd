## Context

C-07 construyó `Asignacion` como entidad y el CRUD individual en `routers/asignaciones.py` + `AsignacionRepository`. C-08 añade las operaciones en bloque que el COORDINADOR necesita para gestionar equipos: mis-equipos, asignación masiva, clonado entre cohortes, modificación de vigencias en bloque y exportación CSV. El modelo de datos no cambia — todas las operaciones son sobre `Asignacion`.

Estado actual: `AsignacionRepository.list_filtrado()` hace listado simple con filtros. No hay operaciones bulk ni clonado.

## Goals / Non-Goals

**Goals:**
- Vista `mis-equipos` resuelta 100% desde el JWT (identidad no paramétrica).
- Asignación masiva atómica: N docentes × 1 contexto en una transacción.
- Clonado de equipo entre cohortes: duplica asignaciones vigentes, no vencidas (RN-12).
- Modificación de vigencias en bloque para un equipo completo.
- Exportación CSV con stdlib (sin dependencias nuevas).
- Autocompletado server-side de usuarios (RN-30) via endpoint de búsqueda.

**Non-Goals:**
- Modificación del modelo `Asignacion` (sin nueva columna ni migración).
- Notificaciones al docente al ser asignado (C-12/C-15 en adelante).
- Importación de asignaciones desde archivo externo.
- Paginación del export (el export es completo).

## Decisions

### D-01: Nuevo router `equipos.py` separado de `asignaciones.py`
Las operaciones de equipo tienen semántica distinta al CRUD individual: operan sobre colecciones y requieren lógica de negocio (clonado, bulk). Mantener el CRUD individual en `asignaciones.py` (sin cambios de C-07) y agregar `equipos.py` como router nuevo con prefijo `/api/v1/equipos`.

Alternativa descartada: extender `asignaciones.py`. Hubiera superado los 500 LOC y mezclado responsabilidades.

### D-02: Lógica de bulk en el repository, no en el router
`clone_equipo`, `bulk_update_vigencia` y `bulk_create` viven en `AsignacionRepository`. Los routers solo orquestan: validan inputs, llaman al repository, auditan. Consistente con la regla dura #11.

### D-03: Clonado solo duplica asignaciones vigentes
RN-12 dice "duplica las asignaciones vigentes". Solo se clonan registros donde `estado_vigencia == "Vigente"` al momento del clonado. Las vencidas se ignoran (son histórico). Si el destino (materia × carrera × cohorte) ya tiene asignaciones para ese usuario+rol, el clon se omite para ese registro (idempotencia parcial).

### D-04: Export CSV con csv stdlib
Sin dependencias nuevas. El endpoint retorna `StreamingResponse` con `media_type="text/csv"` y header `Content-Disposition: attachment`. El CSV incluye: id, usuario_email (desencriptado), rol, materia, carrera, cohorte, comisiones, responsable_email, desde, hasta, estado_vigencia.

Riesgo aceptado: la desencriptación de email en el export requiere llamar al servicio de cifrado para cada fila — aceptable en volúmenes de equipo (< 500 filas típicas).

### D-05: Autocompletado búsqueda en `UserRepository`
`GET /equipos/buscar-docentes?q=<término>&limit=10` delega en un nuevo método `UserRepository.search_by_name(q, roles, limit)` que hace `ILIKE` sobre campos de nombre/apellido. Solo retorna usuarios no eliminados del tenant. Limit máx 50.

### D-06: Auditoría — código existente
`ASIGNACION_MODIFICAR` ya existe en `app/core/audit.py` (verificado en C-07). Las operaciones bulk lo emiten con `filas_afectadas=N`. El clonado emite un evento con el count de asignaciones creadas.

## Risks / Trade-offs

- **[Riesgo] Clonado parcialmente idempotente**: si se llama dos veces con el mismo origen → destino, la segunda llamada no duplica (por la condición de skip). Pero si el destino ya existía por otra vía, puede haber duplicados de mismo usuario+rol. **Mitigación**: el clonado verifica unicidad (usuario_id, rol, materia_id, cohorte_id, tenant_id) antes de insertar; si ya existe (no-deleted), retorna 409 con detalle de conflictos.

- **[Riesgo] Bulk create en transacción larga**: N inserts en una sola transacción puede ser lento para equipos grandes. **Mitigación**: límite de 200 docentes por llamada de asignación masiva (validado en schema Pydantic). Para equipos más grandes, se llama N/200 veces.

- **[Trade-off] Export sin paginación**: para tenants con muchas asignaciones, el CSV puede ser grande. Aceptable para MVP; streaming lo maneja sin cargar todo en memoria.

## Migration Plan

Sin migración de DB (no hay cambios en el modelo). Solo código nuevo. Despliegue directo.

## Open Questions

- ¿El export debe incluir usuarios con asignaciones vencidas o solo vigentes? **Asumido**: todas (incluyendo vencidas del filtro aplicado). El caller puede filtrar por estado en el query.
