## Why

Con padrón (C-09) y calificaciones (C-10) en DB, el paso siguiente del flujo central del PROFESOR es el análisis: quién está atrasado, cómo rankean los alumnos, cuáles son las notas finales. Sin esta capa, los datos importados no generan valor visible. Este change cierra el paso 5 del FL-02 y habilita C-12 (comunicaciones).

## What Changes

- **Endpoint `GET /analisis/atrasados/{asignacion_id}/{materia_id}`**: retorna lista de alumnos atrasados — aquellos con al menos una calificación reprobada o con actividades faltantes (RN-06). Se acompaña del detalle de cada actividad faltante/reprobada para facilitar la selección de destinatarios en C-12.
- **Endpoint `GET /analisis/ranking/{asignacion_id}/{materia_id}`**: retorna ranking de alumnos ordenado por cantidad de actividades aprobadas, excluyendo alumnos sin ninguna aprobada (RN-09).
- **Endpoint `GET /analisis/notas-finales/{asignacion_id}/{materia_id}`**: retorna nota promedio final por alumno, agrupando todas las calificaciones numéricas de la asignación.
- **Sin nuevas tablas**: toda la data ya vive en `calificaciones`, `umbral_materia` y `entrada_padron`.

## Capabilities

### New Capabilities
- `analisis-academico`: endpoints de análisis sobre datos importados — atrasados (RN-06), ranking (RN-09), notas finales (F2.5)

### Modified Capabilities
_(ninguna)_

## Decisions

**D1 — Sin modelo nuevo; análisis 100% derivado de calificaciones**
C-11 no crea tablas. Los cálculos se ejecutan en Python sobre filas ya en DB. Este diseño es correcto para el volumen esperado (comisiones de hasta ~500 alumnos × ~20 actividades).

**D2 — Definición de "faltante": alumno sin calificación en alguna actividad de la comisión**
El conjunto de actividades de referencia se calcula como DISTINCT(actividad) de la asignación × materia. Un alumno falta si no tiene registro para alguna de esas actividades.

**D3 — Atrasado = faltante OR reprobado (RN-06)**
Un alumno es atrasado si tiene al menos una actividad faltante O al menos una calificación con aprobado=False.

**D4 — Ranking solo incluye alumnos con ≥1 aprobada (RN-09)**
Alumnos sin ninguna aprobada no aparecen en el ranking.

**D5 — Permisos: `atrasados:ver`; is_own_resource para PROFESOR**
PROFESOR solo ve datos de sus propias asignaciones. COORDINADOR/ADMIN ven cualquier asignación del tenant.

**D6 — Respuestas paginadas con limit/offset**
Los endpoints de atrasados y ranking aceptan `limit` y `offset` para manejar comisiones grandes.
