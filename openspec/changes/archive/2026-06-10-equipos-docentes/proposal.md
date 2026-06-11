## Why

C-07 construyó el modelo `Asignacion` y el CRUD individual, pero el flujo real del COORDINADOR al inicio de cada cuatrimestre requiere operaciones en bloque sobre equipos completos: clonar, asignar en masa, modificar vigencias y exportar. Sin estas operaciones, cada cuatrimestre implica reconfigurar manualmente cientos de asignaciones.

## What Changes

- **GET /api/v1/equipos/mis-equipos** — Vista del docente autenticado: sus asignaciones activas con carrera, cohorte, materia, rol y estado de vigencia (F4.2).
- **GET /api/v1/equipos** — Listado global de asignaciones del tenant con filtros (materia, carrera, cohorte, usuario, rol, estado); para COORDINADOR/ADMIN (F4.3).
- **GET /api/v1/equipos/buscar-docentes** — Autocompletado server-side de usuarios por nombre/apellido para asignación masiva (RN-30).
- **POST /api/v1/equipos/masiva** — Asignar N docentes en bloque a materia × carrera × cohorte × rol con vigencia definida (F4.4, RN-30).
- **POST /api/v1/equipos/clonar** — Duplicar todas las asignaciones de una combinación origen a un destino con fechas del nuevo período (F4.5, RN-12).
- **PATCH /api/v1/equipos/vigencia** — Actualizar fechas de vigencia de todas las asignaciones de un equipo en una sola operación (F4.6).
- **GET /api/v1/equipos/exportar** — Exportar el equipo completo a CSV con detalle de asignaciones (F4.7).
- Auditoría: cada operación de escritura emite `ASIGNACION_MODIFICAR`.

## Capabilities

### New Capabilities

- `equipo-mis-equipos`: Vista de mis equipos propia del docente autenticado; filtra asignaciones por usuario resuelto del JWT.
- `equipo-asignacion-masiva`: Asignación masiva de N docentes a un contexto con autocompletado de usuarios (RN-30).
- `equipo-clonar`: Clonado de equipo entre cohortes: duplica asignaciones vigentes con fechas del período destino (RN-12).
- `equipo-vigencia-masiva`: Modificación en bloque de vigencia (desde/hasta) de todas las asignaciones de un equipo seleccionado.
- `equipo-export`: Exportación del equipo a CSV descargable con detalle completo de asignaciones.

### Modified Capabilities

- `asignacion-abm`: El router `asignaciones.py` de C-07 queda como CRUD individual; los endpoints de equipo van a un router separado `equipos.py` bajo el prefijo `/api/v1/equipos`.

## Impact

- **Nuevo router**: `backend/app/api/v1/routers/equipos.py` (≤500 LOC — separado por dominio)
- **Extensión del repository**: `AsignacionRepository` suma métodos `list_equipo`, `clone_equipo`, `bulk_update_vigencia` y `bulk_create`
- **Nuevo schema**: `backend/app/schemas/equipos.py`
- **Nuevo audit code**: `ASIGNACION_MODIFICAR` en `app/core/audit.py` (puede ya existir — verificar)
- **Dependencias**: sin nuevas librerías de runtime; exportación CSV con `csv` stdlib
- **Permiso requerido**: `equipos:asignar` (ya en RBAC seed de C-04)
