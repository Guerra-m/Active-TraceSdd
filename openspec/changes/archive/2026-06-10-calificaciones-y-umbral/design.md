## Context

Padrón activo de alumnos (C-09) ya disponible. Las calificaciones importadas del LMS deben vincularse a los alumnos del padrón para habilitar el análisis de atrasados (C-11). El sistema recibe archivos xlsx/csv exportados del LMS de Moodle; el formato tiene columnas `Nombre` y `Apellido(s)` y columnas de actividades cuyos headers terminan en `(Real)` para notas numéricas.

## Goals / Non-Goals

**Goals:**
- Persistir calificaciones (numéricas y textuales) por alumno × actividad × materia con scope de asignación
- Calcular y persistir `aprobado` al momento del import usando el umbral vigente
- Configurar umbral por asignación docente (GET/PUT) con fallback a 60%
- Vaciar calificaciones propias sin afectar las de otros docentes (RN-04)

**Non-Goals:**
- Análisis de atrasados (C-11)
- Exportación de resultados
- Recálculo retroactivo de `aprobado` al cambiar el umbral

## Decisions

**D1 — Tabla `calificaciones` con scope `(asignacion_id, materia_id, actividad, entrada_padron_id)`**
Cada Calificacion referencia la asignación docente que importó el dato. Esto garantiza RN-04: el vaciado filtra por `asignacion_id` del actor. La clave de negocio es `(asignacion_id, actividad, entrada_padron_id)` — única por alumno × actividad × docente.

**D2 — `entrada_padron_id` nullable**
Si no hay padrón activo para la materia al momento de importar, `entrada_padron_id=null`. El sistema sigue importando; el alumno queda sin vínculo a padrón. Esto permite importar calificaciones antes del padrón (flujo de coordinación).

**D3 — Mapeo alumno: email (primer intento) → null (fallback)**
El parser busca `EntradaPadron` por email en la versión activa. Si no encuentra match → `entrada_padron_id=null`. No hay fallback por nombre porque los nombres son ambiguos en CSV del LMS.

**D4 — `aprobado` calculado en servicio, persistido en DB**
El cálculo `aprobado` usa el `UmbralMateria` de la asignación o el default 60%. Se persiste para que C-11 haga queries eficientes sin recalcular.

**D5 — `UmbralMateria` por `asignacion_id` + `materia_id`**
Unique constraint en `(tenant_id, asignacion_id, materia_id)`. Si no existe registro → GET retorna `{"umbral_pct": 60, "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"]}`.

**D6 — valores_aprobatorios como JSONB**
Default en DB: `'["Satisfactorio", "Supera lo esperado"]'::jsonb`. Configurable por docente.

**D7 — permiso `calificaciones:importar` ya existe en seed RBAC**
PROFESOR con is_own_resource=True. COORDINADOR/ADMIN sin is_own_resource. El guard de asignación vigente (`_check_profesor_scope`) ya implementado en C-09 se reutiliza para import y delete.

**D8 — Parser detecta tipo de columna por header**
- Columna termina en ` (Real)` → nota numérica, escala 0-100
- Columna no termina en ` (Real)` y no es metadato (Nombre, Apellido, Email, etc.) → nota textual
- Metadatos estándar: `Nombre`, `Apellido(s)`, `Dirección de correo`, `Número de ID`

## Risks / Trade-offs

- Si el LMS cambia el formato de los headers, el parser puede fallar silenciosamente (mitigation: validación de columnas mínimas con error descriptivo)
- El recálculo de `aprobado` al cambiar el umbral requeriría re-importar; es un diseño intencional (simplicidad sobre consistencia retroactiva)
