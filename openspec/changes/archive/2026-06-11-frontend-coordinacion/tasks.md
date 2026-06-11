# Tasks: frontend-coordinacion

## T-01: Tipos y estructura base del módulo coordinacion
- [x] Crear `frontend/src/features/coordinacion/types/index.ts` con tipos Equipo, Aviso, Tarea, Monitor, EncuentroAdmin, Coloquio, Convocatoria, Comentario, etc.

## T-02: Servicios de coordinacion
- [x] Crear `frontend/src/features/coordinacion/services/equiposService.ts`
- [x] Crear `frontend/src/features/coordinacion/services/avisosService.ts`
- [x] Crear `frontend/src/features/coordinacion/services/tareasService.ts`
- [x] Crear `frontend/src/features/coordinacion/services/monitorService.ts`
- [x] Crear `frontend/src/features/coordinacion/services/encuentrosAdminService.ts`
- [x] Crear `frontend/src/features/coordinacion/services/coloquiosService.ts`

## T-03: Hooks de coordinacion
- [x] Crear `frontend/src/features/coordinacion/hooks/useEquipos.ts` + test
- [x] Crear `frontend/src/features/coordinacion/hooks/useAvisos.ts` + test
- [x] Crear `frontend/src/features/coordinacion/hooks/useTareas.ts` + test
- [x] Crear `frontend/src/features/coordinacion/hooks/useMonitor.ts` + test
- [x] Crear `frontend/src/features/coordinacion/hooks/useEncuentrosAdmin.ts` + test
- [x] Crear `frontend/src/features/coordinacion/hooks/useColoquios.ts` + test

## T-04: Módulo de Equipos docentes
- [x] Crear `EquiposPage.tsx` con listado, asignación masiva, clonar, modificar vigencia, export
- [x] Test `EquiposPage.test.tsx` (happy path + sin permiso)

## T-05: Módulo de Avisos
- [x] Crear `AvisosPage.tsx` con listado, crear, publicar, editar, eliminar, ack
- [x] Test `AvisosPage.test.tsx` (happy path + validación)

## T-06: Módulo de Tareas internas
- [x] Crear `TareasPage.tsx` con listado, crear, delegar, cambio de estado, comentarios
- [x] Test `TareasPage.test.tsx` (happy path + sin tareas)

## T-07: Monitores transversales
- [x] Crear `MonitorPage.tsx` con monitor general y filtro por rango de fechas
- [x] Test `MonitorPage.test.tsx` (happy path + rango inválido)

## T-08: Encuentros (admin)
- [x] Crear `EncuentrosAdminPage.tsx` con vista admin, slots recurrentes, edición de instancias
- [x] Test `EncuentrosAdminPage.test.tsx` (happy path + sin permiso)

## T-09: Coloquios
- [x] Crear `ColoquiosPage.tsx` con listado, crear convocatoria, importar alumnos, métricas
- [x] Test `ColoquiosPage.test.tsx` (happy path + validación cupo)

## T-10: Setup de cuatrimestre (FL-03)
- [x] Crear `SetupCuatrimestrePage.tsx` con wizard: clonar equipo + asignación masiva
- [x] Test `SetupCuatrimestrePage.test.tsx` (happy path + paso inválido)

## T-11: Router y menuConfig
- [x] Agregar rutas de coordinacion en `router.tsx`
- [x] Agregar ítems de coordinacion en `menuConfig.ts`
