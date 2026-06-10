## Context

El padrón es el conjunto de alumnos habilitados para una materia en un período. Hasta C-08 el sistema tiene estructura académica (materias, cohortes) y usuarios con roles, pero ninguna entidad que liste alumnos cursando. Este change crea esa entidad (versionada), el flujo de importación desde archivo, y el adaptador de Moodle WS para sync automatizada.

Contexto técnico:
- Stack: FastAPI async, SQLAlchemy 2.0, PostgreSQL, httpx para cliente async.
- Los archivos se reciben vía `multipart/form-data` (FastAPI `UploadFile`).
- Moodle WS es opcional: si `MOODLE_URL` no está configurado, el endpoint sólo acepta upload manual.
- `EntradaPadron.email` es PII — se cifra con AES-256-GCM (mismo mecanismo que User.email).

## Goals / Non-Goals

**Goals:**
- Modelos `VersionPadron` + `EntradaPadron` con scope de tenant garantizado
- Endpoint de importación que crea nueva versión y desactiva la anterior en una transacción atómica
- Cliente Moodle WS async (httpx) con timeout y mapeo a 502
- Fallback manual (xlsx/csv) que funciona sin configuración de Moodle
- Vaciar padrón activo (soft-delete scope-isolated por (usuario_id, materia_id, cohorte_id))
- Audit `PADRON_CARGAR` en cada importación exitosa

**Non-Goals:**
- Import de calificaciones (C-10)
- Sync automática nocturna scheduleable (infraestructura de scheduler fuera de MVP; el endpoint on-demand es suficiente)
- Resolución automática `usuario_id` para entradas sin cuenta (matching por email se hace en C-10 al importar calificaciones)
- UI de previsualización (backend-only en C-09)

## Decisions

**D1 — Modelo versionado (no upsert destructivo)**
Se adopta E6 del modelo de datos: cada importación crea una `VersionPadron` nueva; activar la nueva desactiva la anterior (soft). El histórico se conserva. Motivo: auditoría, trazabilidad, y el hecho de que Calificaciones (C-10) referencia `EntradaPadron.id` — destruir entradas rompería esas FK.

**D2 — `usuario_id` nullable en EntradaPadron**
Un alumno puede estar en el padrón antes de tener cuenta en el sistema. El matching se hace a posteriori (hook en C-10 o proceso de reconciliación). Nunca se bloquea la importación por alumnos sin cuenta.

**D3 — Email de EntradaPadron cifrado; sin email_hash**
A diferencia de User, no se necesita buscar por email de padrón en queries frecuentes. Solo se descifra cuando se visualiza o reconcilia. No se guarda hash porque el email del padrón no es credencial de acceso.

**D4 — Moodle WS client en `app/integrations/moodle_ws.py`**
Módulo propio con `httpx.AsyncClient`, timeout configurable (default 30s). No se usa requests síncronos. Los errores de red o HTTP >= 500 mapean a `MoodleWSError(502, retry_after=60)`. Si `MOODLE_URL` es vacío, `MoodleWSClient` lanza `MoodleNotConfiguredError` → el router responde 422 con instrucción de usar upload manual.

**D5 — Importación atómica en una sola transacción**
La creación de VersionPadron, inserción de todas las EntradaPadron y desactivación de la versión anterior ocurren en la misma transacción SQLAlchemy. Si cualquier paso falla, se hace rollback completo — no queda padrón parcial.

**D6 — Parsing de xlsx/csv en capa de servicio (no en router)**
El router sólo recibe `UploadFile` y delega parsing a `PadronParser` (función o clase en `app/services/padron_parser.py`). El parser normaliza columnas, detecta encoding (utf-8 con fallback latin-1 para csvs de Windows), y retorna lista de dicts validados por Pydantic.

**D7 — Vaciar = soft-delete de la versión activa, scope-isolated**
`DELETE /padron/{materia_id}/{cohorte_id}` marca `activa=False` en la versión activa de esa combinación para el `tenant_id` del actor (RN-04). No elimina entradas ni otras versiones. Requiere `calificaciones:importar` (PROFESOR sólo su scope; COORDINADOR global).

**D8 — Permisos: is_own_resource para PROFESOR**
`calificaciones:importar` está en la matriz como `is_own_resource=True` para PROFESOR. El sistema verifica que el PROFESOR tenga una `Asignacion` vigente para la `(materia_id, cohorte_id)` del request. COORDINADOR tiene `is_own_resource=False` (acceso global al tenant).

## Risks / Trade-offs

- **[Riesgo] Archivos xlsx grandes (10k+ filas)** → Mitigation: `UploadFile` en streaming con `read()` chunked; inserción en batch de 500 entradas por flush.
- **[Riesgo] Moodle WS timeout o caída** → Mitigation: timeout 30s configurable, respuesta 502 con `retry_after`; el import manual es siempre el fallback.
- **[Riesgo] CSV con encoding windows (latin-1)** → Mitigation: intento utf-8 primero, fallback a latin-1 con warning en logs.
- **[Trade-off] Sin hash para email de padrón** → No hay búsqueda directa por email; se acepta ya que el caso de uso es listar entradas por materia/cohorte, no lookup por email.
- **[Riesgo] is_own_resource para PROFESOR requiere query extra** → verificar Asignacion vigente en cada request de importación; es un JOIN simple, overhead aceptable.

## Migration Plan

- Migración `20260610_007_padron`: CREATE TABLE `version_padron` + CREATE TABLE `entrada_padron`.
- Sin datos a migrar (tablas nuevas).
- Downgrade: DROP TABLE `entrada_padron` → DROP TABLE `version_padron` (en ese orden por FK).

## Open Questions

- ¿El matching de `EntradaPadron.email` con `User.email_hash` se hace automáticamente al importar o bajo demanda? (decisión diferida a C-10 donde se necesita para asociar calificaciones)
- ¿La sync nocturna usa APScheduler, Celery, o un endpoint que el cliente llama con cron? (diferido fuera del MVP de C-09)
