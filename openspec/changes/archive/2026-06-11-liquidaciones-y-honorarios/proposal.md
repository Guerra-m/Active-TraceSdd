# Propuesta: C-18 liquidaciones-y-honorarios

## Qué

Implementar el módulo de liquidaciones y honorarios docentes: cálculo Base + Plus por período (cohorte × mes), cierre inmutable de liquidaciones, gestión de facturas para docentes facturantes, y KPIs financieros para el rol FINANZAS.

## Por qué

El sistema necesita una capa de cálculo de honorarios que consolide la información de asignaciones docentes con tablas de salarios configurables por tenant, cumpliendo los requisitos financieros del producto.

## Alcance

- Campo `grupo_plus` en tabla `materias` (resuelve PA-22)
- Modelos: `SalarioBase`, `SalarioPlus`, `Liquidacion`, `Factura`
- Migraciones Alembic correspondientes
- Repositories y Services con TDD estricto
- Endpoints REST con guard `liquidaciones:*` (rol FINANZAS)
- Cobertura ≥90% de reglas de negocio RN-22 a RN-38

## Fuera de alcance

- Exportación a formatos externos (PDF, Excel)
- Integración directa con sistemas bancarios
