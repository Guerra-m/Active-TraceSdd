## Context

No existen modelos ni endpoints de encuentros o guardias. C-07 provee `Asignacion` (vínculo usuario↔contexto) — los slots y guardias referencian `asignacion_id` para saber quién los crea. La lógica de generación de instancias recurrentes es la única lógica de negocio no trivial de este change.

## Goals / Non-Goals

**Goals:**
- Modelos `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` con migración Alembic.
- Generación atómica de N instancias al crear un slot recurrente (RN-13).
- Edición independiente por instancia sin afectar slot ni hermanas (RN-14).
- Bloque HTML de encuentros (F6.4): generado server-side con f-strings, sin dependencias.
- Vista admin transversal (F6.5) y registro+export de guardias (F6.6).

**Non-Goals:**
- Notificaciones al crear/modificar encuentros (C-12 ya cubre comunicaciones).
- Sincronización automática con el LMS (el HTML se copia manualmente).
- Paginación del export CSV (export completo).
- Reagendamiento automático de instancias canceladas.

## Decisions

### D-01: Generación de instancias recurrentes en el service layer
La lógica de "dado un slot recurrente, generar N instancias" va en un service (`EncuentroService.crear_slot`) y NO en el router. El router valida el payload, llama al service, el service calcula las fechas y delega al repository. Esto mantiene la lógica de negocio testeable sin HTTP.

Fechas generadas: `fecha_inicio + (i × 7 días)` para `i = 0..cant_semanas-1`. Día de semana del slot es solo orientativo (el `dia_semana` en `SlotEncuentro`); la fecha real de cada instancia viene del cálculo aritmético.

### D-02: `slot_id` nullable en `InstanciaEncuentro`
Un encuentro único (RN-13 modo 2) NO genera slot — crea directamente una `InstanciaEncuentro` con `slot_id=NULL`. El slot solo existe en modo recurrente. Esto simplifica el modelo: `InstanciaEncuentro` es la entidad central; el slot es solo metadata de recurrencia.

### D-03: HTML de aula virtual generado con f-strings
`GET /encuentros/aula-virtual` retorna texto HTML sin Jinja ni librerías de templating. El bloque es un `<ul>` con `<li>` por cada instancia programada/realizada con fecha, hora, título, meet_url y video_url. `Content-Type: text/html`.

### D-04: Guardia — roles y scope
El TUTOR puede crear guardias propias y consultar solo las suyas. COORDINADOR y ADMIN consultan global y exportan. El scope se resuelve del JWT: si el usuario tiene solo rol TUTOR, el repository filtra por `asignacion_id` de ese usuario; si tiene COORDINADOR/ADMIN, ve todo el tenant.

Para evitar hardcodear lógica de roles en el router, se pasa `solo_propias=True/False` al repository según el permiso efectivo del usuario resuelto.

### D-05: `dia_semana` como String
Se almacena como `String(10)` con check constraint en lugar de Enum nativo de PostgreSQL — evita problemas de migración si se agrega un valor al enum. Los valores válidos: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo.

### D-06: Export guardias con csv stdlib
Misma decisión que C-08: `StreamingResponse` + `csv.writer` + `StringIO`. Sin dependencias nuevas.

## Risks / Trade-offs

- **[Riesgo] Generación de muchas instancias**: `cant_semanas=52` crea 52 instancias en una sola transacción. **Mitigación**: validar `cant_semanas ≤ 52` en el schema Pydantic.
- **[Trade-off] HTML sin templating**: el bloque HTML es básico (sin estilos ni clases CSS específicas de Moodle). Suficiente para MVP; el frontend puede mejorarlo en C-22.

## Migration Plan

Una migración `20260610_010_encuentros_guardias.py`:
- Tabla `slot_encuentros`: id, tenant_id, asignacion_id, materia_id, titulo, hora, dia_semana, fecha_inicio, cant_semanas, fecha_unica, meet_url, vig_desde, vig_hasta, timestamps, soft delete.
- Tabla `instancias_encuentro`: id, tenant_id, slot_id (nullable FK), materia_id, fecha, hora, titulo, estado, meet_url, video_url, comentario, timestamps, soft delete.
- Tabla `guardias`: id, tenant_id, asignacion_id, materia_id, carrera_id, cohorte_id, dia, horario, estado, comentarios, timestamps, soft delete.

## Open Questions

_(ninguna — scope bien definido en KB)_
