# Proposal: C-24 frontend-finanzas-y-admin

## Qué

Implementar las interfaces de usuario para los módulos de **Finanzas** (rol FINANZAS) y **Administración** (rol ADMIN) en el frontend React de activia-trace.

## Por qué

Los backends de liquidaciones (C-18), auditoría (C-19), estructura académica (C-06) y usuarios (C-07) están implementados. Falta la interfaz gráfica que permita a los roles FINANZAS y ADMIN operar sobre esas funcionalidades.

## Alcance

### Feature FINANZAS (permiso `liquidaciones:*`)
- Vista de liquidaciones del período: selector cohorte+mes, tabla docentes con base/plus/total, segmentación General/NEXO/Facturantes, KPIs arriba
- Calcular liquidación: POST /api/v1/liquidaciones/calcular con preview antes de confirmar
- Cerrar liquidación por docente individual: POST /api/v1/liquidaciones/{id}/cerrar
- Historial de liquidaciones: filtro período/estado con paginación
- Grilla salarial: ABM SalarioBase y SalarioPlus con React Hook Form + Zod
- Facturas: lista con filtros, registrar nueva, marcar como abonada

### Feature ADMIN (permisos `estructura:gestionar`, `auditoria:ver`)
- Estructura académica: ABM Carreras, Cohortes, Materias (campo grupo_plus nullable)
- Usuarios del tenant: lista con estado/rol, edición estado activo/inactivo
- Panel de auditoría: log completo con filtros, KPIs de acciones por día y estado comunicaciones

## Dependencias satisfechas
- C-21 (shell+auth) ✓
- C-18 (liquidaciones backend) ✓
- C-19 (auditoría backend) ✓
- C-06 (estructura backend) ✓
- C-07 (usuarios backend) ✓

## Governance
BAJO — frontend sobre backend CRÍTICO ya implementado. Sin lógica de negocio nueva.
