## Context

La arquitectura frontend usa feature-based modules (`features/{name}/{components,hooks,services,types,pages}`). C-21 (shell + auth) ya provee `RequireAuth`, `RequirePermission`, `AppLayout`, `Sidebar` con `menuConfig.ts`, `AuthContext` con `useAuth()` y el cliente Axios centralizado en `shared/services/api.ts`. Las features de calificaciones (C-10), análisis (C-11) y comunicaciones (C-12) tienen sus endpoints backend disponibles.

## Goals / Non-Goals

**Goals:**
- Módulo `features/academico` completo con 6 sub-features para el rol PROFESOR
- Integración con TanStack Query para server state, React Hook Form + Zod para formularios
- Tests Vitest + Testing Library con TDD (happy path + edge case por componente/hook)
- TypeScript estricto (sin `any`, `noUnusedLocals`, `noUnusedParameters`)
- Rutas protegidas y menú filtrado por permisos

**Non-Goals:**
- Implementación de endpoints backend (ya provistos por C-10/C-11/C-12)
- SSE/WebSocket para tracking en tiempo real (polling con TanStack Query refetchInterval)
- Export PDF (solo CSV para entregas sin corregir)
- Soporte multi-rol en esta feature (solo PROFESOR en esta iteración)

## Decisions

### D-01: Estructura de directorios plana dentro de `academico/`
```
features/academico/
  components/   — componentes compartidos del módulo (tablas, badges, cards)
  hooks/        — TanStack Query hooks (useAtrasados, useImportCalificaciones, etc.)
  services/     — funciones de API (fetchAtrasados, postImportCalificaciones, etc.)
  types/        — tipos TypeScript del dominio académico
  pages/        — páginas enrutables (AtrasadosPage, ImportacionPage, etc.)
```
Alternativa descartada: sub-directorios por sub-feature (importacion/, atrasados/, etc.) — innecesaria complejidad dado el tamaño de la feature.

### D-02: Polling para tracking de comunicación (no SSE)
El backend de C-12 expone `GET /api/comunicaciones/{id}/estado`. Usar `refetchInterval: 3000` en TanStack Query mientras el estado sea `PENDIENTE` o `ENVIANDO`. Esto es suficiente para el caso de uso y evita complejidad de WebSockets.

### D-03: Preview de importación en modal
La importación muestra primero un `GET /api/calificaciones/preview?comision_id=X` para listar actividades disponibles. El usuario selecciona cuáles importar y confirma con `POST /api/calificaciones/import`. El modal maneja el flujo multi-step con estado local (React useState).

### D-04: Export CSV client-side
Para entregas sin corregir, el export CSV se genera en el cliente (transformando la respuesta JSON a CSV con un blob URL). Evita un endpoint dedicado de export.

### D-05: Rutas bajo `/profesor/`
```
/profesor/atrasados
/profesor/importar
/profesor/umbral
/profesor/entregas
/profesor/comunicaciones
/profesor/monitor
```
Todas bajo `<RequireAuth>` en `router.tsx`.

## Risks / Trade-offs

- [Riesgo] Los endpoints `/api/analisis/*` pueden no seguir exactamente la forma asumida → Mitigación: los services tipan la respuesta con interfaces TypeScript; si difieren, solo se actualiza el type + service sin tocar páginas.
- [Riesgo] `refetchInterval` de 3s puede generar carga en el backend → Mitigación: el polling se activa solo cuando `estado === 'PENDIENTE' || estado === 'ENVIANDO'` y se detiene al llegar a estado final.
- [Trade-off] CSV client-side no maneja datasets grandes → aceptable para el caso de uso (entregas de una comisión).

## Open Questions

- ¿La API de preview de calificaciones es `GET /api/calificaciones/preview` o está embebida en el POST? → Asumido como GET separado; si no existe, el POST retorna preview y el flujo se adapta.
