## Why

El rol PROFESOR carece de una interfaz web para gestionar su comisión: no puede importar calificaciones desde Moodle, configurar umbrales de atraso, visualizar el estado de sus alumnos ni enviar comunicaciones a atrasados. Esta feature completa el ciclo docente end-to-end en la plataforma.

## What Changes

- Nueva feature `academico` bajo `frontend/src/features/academico/`
- Página de importación de calificaciones con preview y selección de actividades (consume `POST /api/calificaciones/import`)
- Configuración de umbral por materia (consume `PUT /api/umbrales/{id}`)
- Vista de atrasados con ranking y notas finales (consume `GET /api/analisis/atrasados`, `GET /api/analisis/ranking`, `GET /api/analisis/notas-finales`)
- Detección de entregas sin corregir con export CSV (consume `GET /api/analisis/entregas-sin-corregir`)
- Envío de comunicaciones a atrasados con preview + tracking de estado (consume `POST /api/comunicaciones/`, `GET /api/comunicaciones/{id}/estado`)
- Monitor de seguimiento tutor/profesor (consume `GET /api/analisis/monitor`)
- Nuevas rutas protegidas bajo `/profesor/` en `router.tsx`
- Nuevos ítems de menú en `menuConfig.ts` con permisos `atrasados:ver` y `comunicacion:enviar`

## Capabilities

### New Capabilities
- `importacion-calificaciones`: Importar calificaciones desde Moodle con preview, selección de actividades y confirmación
- `configuracion-umbral`: Configurar el umbral de aprobación por materia/comisión
- `vista-atrasados`: Ver lista de alumnos atrasados, ranking y notas finales con filtros
- `entregas-sin-corregir`: Ver y exportar entregas pendientes de corrección
- `comunicacion-atrasados`: Enviar comunicaciones a alumnos atrasados con preview y tracking
- `monitor-seguimiento`: Monitor unificado de seguimiento tutor/profesor

### Modified Capabilities
<!-- No hay specs existentes de frontend que cambien requisitos -->

## Impact

- `frontend/src/router.tsx`: agregar rutas `/profesor/*`
- `frontend/src/features/layout/menuConfig.ts`: agregar ítems del módulo docente
- Nuevo directorio: `frontend/src/features/academico/`
- APIs backend: las rutas `/api/calificaciones/import`, `/api/umbrales/*`, `/api/analisis/*`, `/api/comunicaciones/*` deben estar disponibles (C-10, C-11, C-12 satisfechos)
