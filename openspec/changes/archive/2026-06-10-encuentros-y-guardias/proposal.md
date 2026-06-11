## Why

El sistema no tiene forma de registrar los encuentros sincrónicos (clases virtuales) ni las guardias de atención de tutores. Los docentes coordinan estos eventos fuera de la plataforma, lo que impide la supervisión del COORDINADOR, la generación del calendario para el LMS y el registro auditable de guardias.

## What Changes

- **POST /api/v1/encuentros/slots** — Crear slot recurrente (N instancias generadas automáticamente) o único (1 instancia), modo excluyente (RN-13). Requiere `encuentros:gestionar`.
- **GET /api/v1/encuentros/slots** — Listar slots del tenant con filtros por materia, asignacion_id.
- **GET /api/v1/encuentros** — Listar instancias con filtros por materia, estado, fecha rango.
- **PATCH /api/v1/encuentros/{id}** — Editar instancia: estado, meet_url, video_url, comentario (RN-14 — independiente del slot).
- **GET /api/v1/encuentros/aula-virtual** — Generar bloque HTML de encuentros programados para copiar al LMS (F6.4).
- **GET /api/v1/encuentros/admin** — Vista transversal de todos los encuentros del tenant (F6.5, COORDINADOR/ADMIN).
- **POST /api/v1/guardias** — Registrar guardia (TUTOR).
- **GET /api/v1/guardias** — Listar guardias con filtros (COORDINADOR/ADMIN: global; TUTOR: propias).
- **GET /api/v1/guardias/exportar** — Exportar guardias a CSV.
- **Migración**: `slot_encuentro`, `instancia_encuentro`, `guardia`.

## Capabilities

### New Capabilities

- `slot-encuentro-abm`: Creación de slots en modo recurrente o único con generación automática de instancias (RN-13).
- `instancia-encuentro-edit`: Edición individual de instancias (estado, meet_url, video_url, comentario) respetando independencia por instancia (RN-14).
- `encuentro-aula-virtual`: Generación de bloque HTML de encuentros para publicar en el LMS (F6.4).
- `encuentros-admin-view`: Vista transversal de encuentros del tenant para supervisión (F6.5) con filtros de materia/estado/fecha.
- `guardia-registro`: Registro de guardias por TUTOR, consulta global + export CSV por COORDINADOR/ADMIN (F6.6).

### Modified Capabilities

_(ninguna — todas son capabilities nuevas)_

## Impact

- **Nuevos modelos**: `backend/app/models/slot_encuentro.py`, `instancia_encuentro.py`, `guardia.py`
- **Nuevos repositories**: `SlotEncuentroRepository`, `InstanciaEncuentroRepository`, `GuardiaRepository`
- **Nuevos routers**: `routers/encuentros.py` + `routers/guardias.py`
- **Nueva migración Alembic**: `20260610_010_encuentros_guardias.py`
- **Nuevo permiso seed**: `encuentros:gestionar` (verificar si ya existe en RBAC seed)
- **Dependencias runtime**: ninguna nueva; export CSV con `csv` stdlib; HTML con f-strings (sin Jinja)
