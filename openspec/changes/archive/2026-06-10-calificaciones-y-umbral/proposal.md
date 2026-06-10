## Why

El flujo central del PROFESOR (importar → analizar → comunicar) requiere como penúltimo paso la ingesta de calificaciones desde el LMS. Sin `Calificacion` y `UmbralMateria`, el análisis de atrasados (C-11) no tiene datos sobre los que operar. Este change cierra el gap entre el padrón (C-09) y el análisis (C-11).

## What Changes

- **Modelo `Calificacion`** (E7): almacena nota numérica y/o textual de un alumno en una actividad evaluable de una materia. Derivado del CSV/XLSX exportado del LMS. El campo `aprobado` se calcula al importar usando el umbral configurado.
- **Modelo `UmbralMateria`** (E8): configuración por asignación docente del criterio de aprobación (umbral %, valores textuales aprobatorios). Si no existe, rige el default del sistema (60%).
- **Parser de calificaciones**: detecta columnas con escala numérica (terminan en `(Real)`, RN-01) y columnas textuales. Mapea alumnos por email contra `EntradaPadron` del padrón activo.
- **Migración 008**: crea `calificaciones` y `umbral_materia`.
- **Endpoints**: importar calificaciones, vaciar datos propios de una materia (RN-04), GET/PUT umbral.

## Capabilities

### New Capabilities
- `calificacion-import`: importar archivo LMS → parsear → persistir Calificaciones vinculadas al padrón activo; vaciar datos de la materia propia (RN-04)
- `umbral-materia`: configurar umbral de aprobación por materia y asignación (RN-03); GET con fallback al default (60%)

### Modified Capabilities
_(ninguna)_

## Decisions

**D1 — scope de calificaciones = `(usuario_id × materia_id)`**
RN-04 establece que el vaciado elimina solo los datos del docente que ejecuta la operación en su materia. Cada `Calificacion` lleva `asignacion_id` (la del docente que importó) para garantizar el scope. PROFESOR con is_own_resource solo ve y vacía sus propias calificaciones.

**D2 — `aprobado` calculado al importar, no derivado en query**
El campo `aprobado: booleano` se persiste en DB para que las queries de atrasados (C-11) sean eficientes. Se recalcula en cada re-importación usando el umbral vigente al momento del import.

**D3 — mapeo alumno por email, fallback por nombre+apellido**
Al importar calificaciones, el sistema busca el `EntradaPadron` de la versión activa del padrón por email. Si no existe padrón activo para la materia, la importación importa igual pero `entrada_padron_id` queda null (alumno sin padrón).

**D4 — columnas numéricas: header termina en `(Real)`**
RN-01. El parser ignora columnas que no terminan en ` (Real)` para las notas numéricas. Las demás columnas no-(Real) con valores textuales son actividades cualitativas.

**D5 — umbral default = 60, configurable por asignación docente**
RN-03. El `UmbralMateria` referencia la `asignacion_id` (no solo materia_id) para que distintos docentes en la misma materia puedan tener umbrales independientes.

**D6 — valores aprobatorios como JSONB, default = ["Satisfactorio", "Supera lo esperado"]**
La lista de valores textuales aprobatorios se almacena en JSONB para permitir configuración por tenant sin cambios de schema. El default hardcoded sigue RN-02.
