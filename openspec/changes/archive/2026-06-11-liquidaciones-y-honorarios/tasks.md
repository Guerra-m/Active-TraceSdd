# Tasks: C-18 liquidaciones-y-honorarios

## Fase 1 — Schema y modelos

- [x] 1.1 Agregar campo `grupo_plus` (nullable VARCHAR 50) a `Materia` model
- [x] 1.2 Crear migración `20260611_016_materia_grupo_plus.py`
- [x] 1.3 Crear modelo `SalarioBase` y `SalarioPlus` en `backend/app/models/salario.py`
- [x] 1.4 Crear modelo `Liquidacion` en `backend/app/models/liquidacion.py`
- [x] 1.5 Crear modelo `Factura` en `backend/app/models/factura.py`
- [x] 1.6 Crear migración `20260611_017_liquidaciones.py` con todas las tablas nuevas
- [x] 1.7 Registrar modelos nuevos en `backend/app/models/__init__.py`

## Fase 2 — Repositories

- [x] 2.1 Crear `SalarioRepository` en `backend/app/repositories/salario_repository.py`
- [x] 2.2 Crear `LiquidacionRepository` en `backend/app/repositories/liquidacion_repository.py`
- [x] 2.3 Crear `FacturaRepository` en `backend/app/repositories/factura_repository.py`

## Fase 3 — Service (lógica de negocio)

- [x] 3.1 Crear `LiquidacionService` en `backend/app/services/liquidacion_service.py`
  - método `calcular_monto(usuario, rol, cohorte_id, periodo, db, tenant_id)` — RN-34
  - método `cerrar_liquidacion(liquidacion_id, actor_id, db, tenant_id)` — RN-22
  - método `get_kpis(periodo, cohorte_id, db, tenant_id)` — RN-38

## Fase 4 — Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/liquidaciones.py` con todos los schemas

## Fase 5 — Routers

- [x] 5.1 Crear `backend/app/api/v1/routers/liquidaciones.py`
- [x] 5.2 Crear `backend/app/api/v1/routers/salarios.py`
- [x] 5.3 Crear `backend/app/api/v1/routers/facturas.py`
- [x] 5.4 Registrar los 3 routers en `backend/app/main.py`

## Fase 6 — Tests TDD

- [x] 6.1 `test_calculo_liquidacion_base_plus()` — fórmula Base + N×Plus
- [x] 6.2 `test_acumulacion_plus_n_comisiones()` — 3 comisiones = 3×Plus
- [x] 6.3 `test_cierre_liquidacion_inmutable()` — cerrada no permite modificación
- [x] 6.4 `test_facturante_excluido_de_liquidacion()` — docente facturador excluido
- [x] 6.5 `test_kpi_segmentacion()` — KPIs separan general/NEXO/facturantes
- [x] 6.6 `test_vigencia_salario()` — toma salario vigente al período
