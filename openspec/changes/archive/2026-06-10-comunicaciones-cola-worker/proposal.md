## Why

Con análisis de atrasados disponible (C-11), el PROFESOR puede identificar a quiénes comunicar. C-12 cierra el flujo central: permite redactar un mensaje, ver la vista previa, enviarlo a los alumnos atrasados y rastrear el estado de cada envío. Sin este change, el sistema detecta problemas pero no puede actuar sobre ellos.

## What Changes

- **Preview** (`POST /comunicaciones/preview`): recibe asunto + cuerpo con variables de sustitución (`{{nombre}}`, `{{apellidos}}`) y retorna el cuerpo renderizado con datos de ejemplo. No persiste nada.
- **Lote y envío** (`POST /comunicaciones/lotes`): crea un `LoteComunicacion` + N registros `Comunicacion` en estado `Pendiente`. Si el lote supera el umbral de volumen, se marca `requiere_aprobacion=True` y permanece en espera.
- **Aprobación** (`POST /comunicaciones/lotes/{lote_id}/aprobar`): solo rol `comunicacion:aprobar`. Transiciona el lote a `Aprobado`; el worker lo procesa.
- **Cancelación** (`DELETE /comunicaciones/lotes/{lote_id}`): cancela mensajes `Pendiente` del lote.
- **Listado** (`GET /comunicaciones/lotes`): lista lotes del tenant/asignación con su estado.
- **Worker**: tarea asyncio en background (`workers/comunicacion_worker.py`) que consume mensajes `Pendiente` (listos para despacho), los transiciona a `Enviando → Enviado / Error`. En dev usa un sender stub que escribe a log.

## Capabilities

### New Capabilities
- `comunicaciones`: ciclo de vida completo de mensajes salientes con máquina de estados (RN-15), preview (RN-16), aprobación configurable (RN-17)

### Modified Capabilities
- `main.py`: lifespan inicia el worker background task

## Decisions

**D1 — Tabla `lotes_comunicacion` separada de `comunicaciones`**
E21 describe `Comunicacion` con `lote_id` como UUID desnudo. Agregamos `lotes_comunicacion` como entidad propia para trackear el estado del lote (incluyendo aprobación) sin tener que consultar N filas. Más eficiente y permite controlar el ciclo de vida a nivel de lote atómicamente.

**D2 — Umbral de aprobación: configurable por tenant en `settings` (default 10)**
`requiere_aprobacion=True` si `len(destinatarios) > settings.comunicacion_umbral_aprobacion`. Permite que tenants pequeños envíen sin aprobación.

**D3 — Destinatario cifrado (RN-12, E21)**
`Comunicacion.destinatario` almacena el email del alumno cifrado con AES-256-GCM. El worker descifra en memoria para llamar al sender. Nunca se expone en ninguna respuesta de API.

**D4 — Worker: asyncio background task en el mismo proceso (MVP)**
Por simplicidad de deploy en Easypanel, el worker corre como `asyncio.Task` en el lifespan del proceso FastAPI. Pollea DB cada `settings.worker_poll_interval_s` (default 10s). No requiere Redis ni celery para el MVP.

**D5 — Sender stub en dev/test (`EMAIL_BACKEND=stub`)**
Cuando `EMAIL_BACKEND=stub`, el worker escribe el mensaje a log en lugar de SMTP real. Los tests usan este backend para verificar la máquina de estados sin infraestructura de email.

**D6 — `asunto` y `cuerpo` se persisten renderizados en cada Comunicacion**
La plantilla (template con `{{variables}}`) se guarda en el lote; cada `Comunicacion` guarda asunto y cuerpo ya interpolados con los datos del alumno. Facilita auditoría y evita re-renderizar al reintentar.
