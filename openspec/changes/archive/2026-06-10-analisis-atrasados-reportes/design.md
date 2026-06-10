## Architecture

Capa de análisis sobre datos ya persistidos en C-09/C-10. Sin nuevas tablas. Tres funciones de servicio + tres endpoints GET.

```
Router (analisis.py)
  └── AnalisisService (analisis_service.py)
        ├── get_atrasados()    → queries calificaciones + entrada_padron
        ├── get_ranking()      → aggregation calificaciones GROUP BY alumno
        └── get_notas_finales()→ average nota_numerica GROUP BY alumno
```

## Decisions

### D1 — Identidad del alumno vía entrada_padron_id

Los tres endpoints filtran solo alumnos con `entrada_padron_id IS NOT NULL`. El email y nombre vienen de `EntradaPadron` (join). Alumnos importados sin padrón activo (C-10) no aparecen en los reportes de análisis — son calificaciones huérfanas sin identidad resoluble.

### D2 — Cálculo de atrasados en Python, no en SQL puro

El algoritmo de "faltante" requiere el conjunto de referencia de actividades (DISTINCT(actividad) para asignacion × materia) y luego detectar alumnos sin calificación para alguna de esas actividades. Se hace en dos queries + lógica Python: query 1 devuelve todas las calificaciones; query 2 devuelve todas las entradas del padrón activo. La intersección y el cálculo de faltantes se realiza en memoria (escala hasta ~500 alumnos × ~20 actividades = 10 000 filas, aceptable).

### D3 — Ranking: COUNT(aprobado=True) DESC

RN-09: solo alumnos con ≥ 1 aprobada. El ranking no pondera actividades entre sí (peso uniforme). Empate → orden por apellidos ASC (determinístico).

### D4 — Nota final: promedio de notas numéricas

Solo nota_numerica se promedia (Decimal). Actividades textuales se excluyen del cálculo numérico pero se informa su count de aprobadas. Si un alumno no tiene ninguna nota numérica, su promedio es null.

### D5 — Permiso: `atrasados:ver`

Permiso propio del módulo de análisis. PROFESOR: is_own_resource=True (solo sus asignaciones). COORDINADOR/ADMIN: is_own_resource=False. Migration 009 agrega solo el seed RBAC (sin nuevas tablas).

### D6 — Email no se retorna en la respuesta

EntradaPadron.email_encrypted se descifra para indexar internamente pero NUNCA se incluye en la respuesta de la API. La respuesta expone solo nombre, apellidos.

## Query Design

### get_atrasados

```sql
-- Query 1: todas las calificaciones activas del scope
SELECT c.id, c.actividad, c.aprobado, c.entrada_padron_id,
       ep.nombre, ep.apellidos
FROM calificaciones c
JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
WHERE c.tenant_id = :tid
  AND c.asignacion_id = :asig_id
  AND c.materia_id = :mat_id
  AND c.deleted_at IS NULL
  AND c.entrada_padron_id IS NOT NULL
ORDER BY ep.apellidos, ep.nombre, c.actividad
```

Post-process en Python:
1. Agrupar por entrada_padron_id
2. Detectar actividades faltantes (set de actividades de referencia − set del alumno)
3. Detectar reprobadas (aprobado=False)
4. Alumno es atrasado si len(faltantes) > 0 OR len(reprobadas) > 0

### get_ranking

```sql
SELECT c.entrada_padron_id,
       ep.nombre, ep.apellidos,
       COUNT(*) FILTER (WHERE c.aprobado = true) AS aprobadas,
       COUNT(*) AS total
FROM calificaciones c
JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
WHERE c.tenant_id = :tid
  AND c.asignacion_id = :asig_id
  AND c.materia_id = :mat_id
  AND c.deleted_at IS NULL
  AND c.entrada_padron_id IS NOT NULL
GROUP BY c.entrada_padron_id, ep.nombre, ep.apellidos
HAVING COUNT(*) FILTER (WHERE c.aprobado = true) > 0
ORDER BY aprobadas DESC, ep.apellidos ASC
```

### get_notas_finales

```sql
SELECT c.entrada_padron_id,
       ep.nombre, ep.apellidos,
       AVG(c.nota_numerica) AS promedio,
       COUNT(*) FILTER (WHERE c.aprobado = true) AS aprobadas,
       COUNT(*) AS total
FROM calificaciones c
JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
WHERE c.tenant_id = :tid
  AND c.asignacion_id = :asig_id
  AND c.materia_id = :mat_id
  AND c.deleted_at IS NULL
  AND c.entrada_padron_id IS NOT NULL
GROUP BY c.entrada_padron_id, ep.nombre, ep.apellidos
ORDER BY ep.apellidos ASC
```
