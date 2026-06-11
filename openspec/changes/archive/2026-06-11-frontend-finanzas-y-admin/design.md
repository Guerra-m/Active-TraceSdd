# Design: C-24 frontend-finanzas-y-admin

## Estructura de directorios

```
frontend/src/features/
├── finanzas/
│   ├── types/index.ts           — Liquidacion, SalarioBase, SalarioPlus, Factura, KPIs
│   ├── services/
│   │   ├── liquidacionesService.ts
│   │   ├── salariosService.ts
│   │   └── facturasService.ts
│   ├── hooks/
│   │   ├── useLiquidaciones.ts
│   │   ├── useSalarios.ts
│   │   └── useFacturas.ts
│   ├── pages/
│   │   ├── LiquidacionesPage.tsx
│   │   ├── GrillaSalarialPage.tsx
│   │   └── FacturasPage.tsx
│   └── components/
│       ├── LiquidacionesTable.tsx
│       ├── KPICards.tsx
│       └── ConfirmCalcularModal.tsx
└── admin/
    ├── types/index.ts           — Carrera, Cohorte, Materia, UsuarioAdmin, AuditLog
    ├── services/
    │   ├── estructuraService.ts
    │   ├── usuariosAdminService.ts
    │   └── auditoriaService.ts
    ├── hooks/
    │   ├── useEstructura.ts
    │   ├── useUsuariosAdmin.ts
    │   └── useAuditoria.ts
    ├── pages/
    │   ├── EstructuraAcademicaPage.tsx
    │   ├── UsuariosAdminPage.tsx
    │   └── AuditoriaPage.tsx
    └── components/
        ├── CarreraForm.tsx
        ├── CohorteForm.tsx
        ├── MateriaForm.tsx
        └── AuditLogTable.tsx
```

## Convenciones

- PascalCase componentes/archivos React
- Sin `any`, sin class components
- Todo fetch via `api` de `@/shared/services/api`
- React Hook Form + Zod para formularios
- TanStack Query para server state
- Tailwind para estilos
- Tests con Vitest + @testing-library/react

## Rutas nuevas (router.tsx)

```
/finanzas/liquidaciones     — LiquidacionesPage
/finanzas/grilla-salarial   — GrillaSalarialPage
/finanzas/facturas          — FacturasPage
/admin/estructura           — EstructuraAcademicaPage
/admin/usuarios             — UsuariosAdminPage
/admin/auditoria            — AuditoriaPage
```

## Endpoints consumidos

### Finanzas
- GET  /api/v1/liquidaciones/           — lista/historial
- GET  /api/v1/liquidaciones/kpis       — KPIs
- POST /api/v1/liquidaciones/calcular   — calcular
- POST /api/v1/liquidaciones/{id}/cerrar — cerrar
- GET/POST/PUT /api/v1/salarios/base    — grilla base
- GET/POST/PUT /api/v1/salarios/plus    — grilla plus
- GET/POST /api/v1/facturas/            — lista + crear
- PUT /api/v1/facturas/{id}/abonar      — marcar abonada

### Admin
- GET/POST/PUT/DELETE /api/v1/admin/carreras
- GET/POST/PUT/DELETE /api/v1/admin/cohortes
- GET/POST/PUT/DELETE /api/v1/admin/materias
- GET/PATCH /api/v1/admin/usuarios
- GET /api/v1/auditoria/
- GET /api/v1/auditoria/panel

## menuConfig.ts

Agregar secciones "Finanzas" y "Administración" con permisos correspondientes.
