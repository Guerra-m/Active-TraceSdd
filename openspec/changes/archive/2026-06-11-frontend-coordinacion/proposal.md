## Why

COORDINADOR y ADMIN necesitan una interfaz centralizada para gestionar equipos docentes, avisos institucionales, tareas internas, monitores de seguimiento, encuentros y coloquios. Sin estas pantallas, la coordinación académica carece de herramienta propia y los flujos operativos (setup de cuatrimestre, asignación masiva, convocatorias a coloquio) deben hacerse manualmente fuera del sistema.

## What Changes

- Nueva feature `coordinacion` bajo `src/features/coordinacion/` con páginas para COORDINADOR/ADMIN
- **Equipos docentes**: listado mis-equipos, asignación masiva de tutores, clonar equipo entre períodos, modificar vigencia en bloque, exportar
- **Avisos**: ABM con scope Global/PorMateria/PorCohorte/PorRol, publicación, filtro de vigencia, confirmación de lectura/ack
- **Tareas internas**: listado propias, asignar/delegar, cambio de estado + comentarios (workflow asincrónico)
- **Monitores transversales**: monitor general (F2.7), seguimiento de coordinación con rango de fechas (F2.9)
- **Encuentros (admin)**: vista admin, slots recurrentes, edición de instancias
- **Coloquios**: crear convocatoria, importar alumnos, listado, panel de métricas
- **Setup de cuatrimestre (FL-03)**: flujo combinado clonar equipo + asignación masiva
- Nuevas rutas en `router.tsx` bajo `<RequireAuth>` con guards de permiso
- Nuevos ítems de menú en `menuConfig.ts`

## Capabilities

### New Capabilities
- `coordinacion-equipos`: Gestión de equipos docentes (asignación, clonar, vigencia, export) para COORDINADOR/ADMIN
- `coordinacion-avisos`: ABM avisos institucionales con scope, publicación y confirmación de lectura
- `coordinacion-tareas`: Tareas internas con workflow asincrónico (asignar, delegar, estados, comentarios)
- `coordinacion-monitores`: Monitores transversales (monitor general y seguimiento de coordinación)
- `coordinacion-encuentros`: Vista admin de encuentros con slots recurrentes y edición de instancias
- `coordinacion-coloquios`: Convocatorias a coloquio, importación de alumnos y panel de métricas

### Modified Capabilities
- `frontend-shell`: Agregar rutas de coordinación al router y nuevos ítems al menuConfig

## Impact

- `frontend/src/features/coordinacion/` — módulo nuevo completo
- `frontend/src/router.tsx` — nuevas rutas protegidas
- `frontend/src/features/layout/menuConfig.ts` — nuevos ítems de menú
- Consume: `/api/equipos/*`, `/api/avisos/*`, `/api/tareas/*`, `/api/analisis/monitor`, `/api/encuentros/*`, `/api/coloquios/*`
- Permisos requeridos: `equipos:asignar`, `avisos:publicar`, `tareas:gestionar`, `encuentros:gestionar`, `atrasados:ver`, `coloquios:read`
- Sin cambios de backend (C-08, C-13, C-14, C-15, C-16 ya implementados)
