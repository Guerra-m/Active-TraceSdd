## Why

El sistema necesita conocer qué alumnos están cursando cada materia en cada cohorte para poder analizar calificaciones, detectar atrasados y enviar comunicaciones. Sin un padrón importado y vinculado a la estructura académica (materia × cohorte), todas las funcionalidades de seguimiento (C-10 en adelante) carecen de datos. El padrón es el dato base: sin él, el sistema no tiene alumnos sobre los cuales operar.

## What Changes

- **Nuevo modelo `VersionPadron`**: registra una versión de padrón para una combinación materia × cohorte × tenant. Versionado: activar una nueva versión desactiva la anterior (el histórico se conserva).
- **Nuevo modelo `EntradaPadron`**: cada fila del padrón — alumno con nombre, apellidos, email [cifrado], comisión, regional, y referencia opcional a un `User` (`usuario_id` nullable si el alumno aún no tiene cuenta en el sistema).
- **Endpoint de importación** `POST /api/v1/padron/importar`: acepta archivo `.xlsx` o `.csv`, crea nueva versión, inserta entradas, desactiva versión anterior, registra `PADRON_CARGAR` en audit log.
- **Endpoint de vaciar** `DELETE /api/v1/padron/{materia_id}/{cohorte_id}`: soft-delete de la versión activa (RN-04, scope-isolated por usuario).
- **Cliente Moodle WS** (`integrations/moodle_ws.py`): adaptador para Moodle Web Services que expone sync de usuarios/padrón vía API estándar del LMS. Sync on-demand desde endpoint + sync nocturna scheduleable. Errores HTTP mapean a 502 con campo `retry_after`.
- **Fallback manual**: cuando el tenant no tiene Moodle WS configurado, la misma ruta de importación acepta xlsx/csv con la convención de columnas definida.
- **Migración 007**: tablas `version_padron` y `entrada_padron`.

> **Nota de consistencia**: RN-05 ("upsert destructivo, sin historial") contradice E6 del modelo de datos ("versionado, historial conservado") y la descripción de C-09 en CHANGES.md. Se adopta el modelo **versionado** (E6 + CHANGES.md) como fuente de verdad. La UI puede presentar el comportamiento como "reemplazo" del punto de vista del usuario, pero internamente la versión anterior se desactiva (no se borra).

## Capabilities

### New Capabilities

- `padron-ingesta`: modelos VersionPadron + EntradaPadron, endpoint de importación (xlsx/csv), versionado (activar nueva → desactiva anterior), endpoint vaciar, email de entrada cifrado con AES-256, audit PADRON_CARGAR.
- `moodle-ws-client`: adaptador Moodle Web Services, sync on-demand y nocturna, mapeo de errores a 502 + `retry_after`, fallback a importación manual cuando WS no está configurado.

### Modified Capabilities

_(ninguna — PADRON_CARGAR ya está en el catálogo de audit constants desde C-05)_

## Impact

- **DB**: 2 tablas nuevas (`version_padron`, `entrada_padron`); migración 007.
- **Nuevos archivos**: `app/models/version_padron.py`, `app/models/entrada_padron.py`, `app/repositories/version_padron_repository.py`, `app/repositories/entrada_padron_repository.py`, `app/api/v1/routers/padron.py`, `app/integrations/moodle_ws.py`, `app/schemas/padron.py`.
- **Dependencias Python**: `openpyxl` (xlsx), `python-multipart` (file upload FastAPI), `httpx` (Moodle WS client async).
- **Permisos requeridos**: `calificaciones:importar` (PROFESOR, is_own_resource; COORDINADOR, global).
- **PII**: `EntradaPadron.email` almacenado cifrado (AES-256-GCM); nunca en texto plano en DB ni logs.
- **Crítico para**: C-10 (calificaciones), C-11 (atrasados), C-12 (comunicaciones).
