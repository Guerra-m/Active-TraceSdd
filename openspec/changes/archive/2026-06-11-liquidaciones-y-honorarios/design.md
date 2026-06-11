# Design: C-18 liquidaciones-y-honorarios

## Decisiones de diseño

### D1 — Fórmula de cálculo
`Total = Base(rol, período) + Σ(Plus(grupo_plus, rol) × N_comisiones_del_grupo)`
- N_comisiones = cantidad de asignaciones vigentes en el período cuyas materias tienen ese grupo_plus
- Acumulación ilimitada (PA-23 resuelto): 3 comisiones de PROG → 3 × Plus(PROG, rol)

### D2 — Vigencia de salarios
- Se toma el salario con mayor `desde` que sea ≤ primer día del período (AAAA-MM)
- Si no hay registro vigente → error de cálculo (no se genera liquidación)

### D3 — Estado de liquidación
- `Abierta`: editable, se puede recalcular
- `Cerrada`: inmutable, genera entrada en audit_log (LIQUIDACION_CERRAR)

### D4 — Docentes facturantes
- `facturador=True` en User → `excluido_por_factura=True` en Liquidacion
- No se incluyen en el cálculo Base+Plus estándar

### D5 — Arquitectura Clean
- Flujo: Router → LiquidacionService → LiquidacionRepository / SalarioRepository
- Toda la lógica de cálculo vive en `LiquidacionService.calcular_periodo()`
- Los repositories solo hacen CRUD con scope de tenant

## Estructura de archivos

```
backend/app/models/
  salario.py          — SalarioBase, SalarioPlus
  liquidacion.py      — Liquidacion
  factura.py          — Factura

backend/app/repositories/
  salario_repository.py
  liquidacion_repository.py
  factura_repository.py

backend/app/services/
  liquidacion_service.py   — lógica de cálculo y cierre

backend/app/schemas/
  liquidaciones.py

backend/app/api/v1/routers/
  liquidaciones.py
  salarios.py
  facturas.py

backend/alembic/versions/
  20260611_016_materia_grupo_plus.py
  20260611_017_liquidaciones.py

backend/tests/
  test_liquidaciones.py
```
