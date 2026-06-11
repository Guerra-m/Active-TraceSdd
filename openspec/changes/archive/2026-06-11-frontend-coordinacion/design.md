## Context

El frontend ya tiene su shell (`C-21`) con auth, routing base, layout y RequirePermission. El backend de equipos (C-08), encuentros (C-13), coloquios (C-14), avisos (C-15) y tareas (C-16) está implementado. Este change agrega las vistas del COORDINADOR/ADMIN sobre esos endpoints ya existentes.

Estructura de referencia ya establecida en el proyecto:
- Feature-based modules: `features/{name}/{components,hooks,services,types,pages}`
- TanStack Query para server state
- React Hook Form + Zod para formularios
- Axios client centralizado en `@/shared/services/api`
- Guards: `RequirePermission` + `RequireAuth`

## Goals / Non-Goals

**Goals:**
- Implementar las 6 sub-módulos de coordinación bajo `features/coordinacion/`
- Registrar todas las rutas en `router.tsx`
- Agregar ítems al menú de coordinación en `menuConfig.ts`
- TDD estricto: test por componente/hook (happy path + edge case)
- TypeScript estricto (sin `any`)

**Non-Goals:**
- Modificar endpoints de backend
- Implementar lógica de negocio fuera de lo que ya proveen los APIs
- Crear nuevos permisos (usar los ya definidos: `equipos:asignar`, `avisos:publicar`, `tareas:gestionar`, `encuentros:gestionar`, `atrasados:ver`, `coloquios:read`)

## Decisions

### D-1: Estructura de módulo única `coordinacion/`
Todos los sub-módulos viven bajo `features/coordinacion/` con sub-carpetas por dominio:
```
features/coordinacion/
  components/       — componentes compartidos de coordinación
  hooks/            — useEquipos, useAvisos, useTareas, useMonitor, useEncuentrosAdmin, useColoquios
  services/         — funciones que llaman a api (coordinacionService.ts)
  types/            — tipos TypeScript del dominio
  pages/            — EquiposPage, AvisosPage, TareasPage, MonitorPage, EncuentrosAdminPage, ColoquiosPage, SetupCuatrimestrePage
```
Alternativa rechazada: una carpeta por dominio (`features/equipos/`, `features/avisos/`, etc.) — fragmentaría las vistas del COORDINADOR que ya existen separadas en otras features; todas las vistas de coordinación van juntas.

### D-2: Un archivo de servicio por dominio dentro de coordinación
`services/equiposService.ts`, `services/avisosService.ts`, etc. Cada uno exporta funciones puras que llaman a `api`. Los hooks de React Query los consumen.
Alternativa rechazada: un solo `coordinacionService.ts` — se vuelve monolítico conforme crece.

### D-3: Paginación server-side con parámetros `page` y `page_size`
Los listados usan `useQuery` con `queryKey` que incluye los filtros y la página. Esto permite invalidar con precisión.

### D-4: Formularios con React Hook Form + Zod
Todos los formularios de creación/edición usan RHF con resolver de Zod. El schema Zod también sirve como tipo derivado con `z.infer<>`.

### D-5: Agrupación de menú con sección "Coordinación"
Se extiende `MenuItem` con campo opcional `section?: string` para agrupar ítems en la sidebar, o se usan separadores por convención. Alternativa simple: lista plana con los nuevos ítems insertados — más simple, se adopta esta.

## Risks / Trade-offs

- [Los endpoints de backend pueden no estar en producción] → Los servicios de frontend retornan promesas; los hooks muestran `isLoading`/`isError` con feedback al usuario. Funciona en modo UI-only mientras el backend se levanta.
- [Sin datos reales para testear flows complejos como clonar equipo] → Tests con `vi.fn()` mockean `api.get`/`api.post`. Se prueban flujos de UI, no integración real.
- [FL-03 Setup de cuatrimestre combina múltiples llamadas] → Se implementa como wizard de pasos secuenciales con estado local; si un paso falla el usuario puede reintentar desde ese paso.

## Migration Plan

1. Crear estructura de directorios bajo `features/coordinacion/`
2. Implementar types primero (sin dependencias)
3. Implementar services (dependen de `api`)
4. Implementar hooks (dependen de services)
5. Implementar components (dependen de hooks)
6. Implementar pages (ensamblan components)
7. Actualizar `router.tsx` con las nuevas rutas
8. Actualizar `menuConfig.ts` con los nuevos ítems
9. Tests junto a cada archivo implementado

## Open Questions

- Ninguna: las dependencias de backend están satisfechas y los permisos son conocidos.
