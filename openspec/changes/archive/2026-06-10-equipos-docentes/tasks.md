## 1. Seguridad y Safety Net

- [x] 1.1 Verificar que el permiso `equipos:asignar` existe en el RBAC seed (C-04) — no agregar si ya está
- [x] 1.2 Verificar que `ASIGNACION_MODIFICAR` existe en `app/core/audit.py` — agregar constante solo si falta
- [x] 1.3 Ejecutar test suite existente (baseline): capturar N tests pasando antes de cualquier cambio

## 2. Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/equipos.py` con `MisEquiposFilters`, `AsignacionMasivaRequest` (lista 1–200 usuario_ids, contexto, vigencia), `ClonarEquipoRequest` (origen, destino, fechas), `VigenciaMasivaRequest` (contexto + desde/hasta opcionales), `BuscarDocentesResponse`
- [x] 2.2 Todos los schemas con `model_config = ConfigDict(extra='forbid')` y validadores para límite 200 y term 2+ chars

## 3. Repository — Métodos Bulk

- [x] 3.1 Agregar `bulk_create(items: list[Asignacion])` a `AsignacionRepository`: inserta lista en una transacción, retorna lista creada
- [x] 3.2 Agregar `clone_equipo(materia_id, carrera_id, cohorte_origen_id, cohorte_destino_id, desde, hasta, tenant_id)`: filtra vigentes en origen, detecta conflictos en destino, retorna `(creadas, conflictos)`
- [x] 3.3 Agregar `bulk_update_vigencia(materia_id, carrera_id, cohorte_id, desde, hasta)` a `AsignacionRepository`: UPDATE con filtro de equipo + `deleted_at IS NULL`, retorna count
- [x] 3.4 Agregar `list_equipo(materia_id, carrera_id, cohorte_id, rol, estado_vigencia)` para listado de equipo con filtros compuestos
- [x] 3.5 Agregar `search_by_name(q, limit)` a `UserRepository`: ILIKE sobre nombre/apellido, retorna lista de usuarios no eliminados del tenant

## 4. Tests — RED primero (TDD)

- [x] 4.1 `test_equipos.py` — test mis-equipos retorna solo asignaciones del JWT (RED)
- [x] 4.2 `test_equipos.py` — test mis-equipos ignora query param usuario_id externo (RED)
- [x] 4.3 `test_equipos.py` — test asignación masiva exitosa (1 usuario, 3 usuarios) (RED)
- [x] 4.4 `test_equipos.py` — test asignación masiva rechaza >200 usuarios (RED)
- [x] 4.5 `test_equipos.py` — test asignación masiva rechaza usuario fuera de tenant (RED)
- [x] 4.6 `test_equipos.py` — test clonado exitoso: solo vigentes se clonan (RED)
- [x] 4.7 `test_equipos.py` — test clonado con conflictos: omite duplicados, retorna lista conflictos (RED)
- [x] 4.8 `test_equipos.py` — test clonado rechaza origen == destino (RED)
- [x] 4.9 `test_equipos.py` — test vigencia masiva actualiza N filas, ignora soft-deleted (RED)
- [x] 4.10 `test_equipos.py` — test vigencia masiva sin campos retorna 422 (RED)
- [x] 4.11 `test_equipos.py` — test buscar-docentes con término válido (RED)
- [x] 4.12 `test_equipos.py` — test buscar-docentes con término < 2 chars retorna 422 (RED)
- [x] 4.13 `test_equipos.py` — test export CSV: status 200, content-type text/csv, columnas correctas (RED)
- [x] 4.14 `test_equipos.py` — test export tenant isolation: solo filas del tenant en el CSV (RED)

## 5. Router — Implementación (GREEN)

- [x] 5.1 Crear `backend/app/api/v1/routers/equipos.py` con prefijo `/api/v1/equipos` y todos los endpoints:
  - `GET /mis-equipos` (identity del JWT, filtros opcionales)
  - `GET /` (listado global, COORDINADOR/ADMIN)
  - `GET /buscar-docentes` (autocompletado)
  - `POST /masiva` (asignación masiva)
  - `POST /clonar` (clonar entre cohortes)
  - `PATCH /vigencia` (vigencia masiva)
  - `GET /exportar` (StreamingResponse CSV)
- [x] 5.2 Registrar `equipos.router` en `app/main.py`
- [x] 5.3 Todos los endpoints con `require_permission("equipos:asignar")` e identidad desde JWT
- [x] 5.4 Cada operación de escritura emite `audit(ASIGNACION_MODIFICAR, filas_afectadas=N)` con el `current_user`

## 6. Export CSV

- [x] 6.1 Implementar función `generar_csv_equipo(asignaciones, session)` en el servicio o directamente en el router (inline si < 50 LOC): usa `csv.writer` con `StringIO`, desencripta emails con `decrypt_value`
- [x] 6.2 El endpoint de export usa `StreamingResponse` con generator para no cargar todo en memoria

## 7. Triangulación y Cobertura

- [x] 7.1 Triangular test mis-equipos: segundo caso con 2 tenants (tenant B no ve datos de A)
- [x] 7.2 Triangular test clonado: caso con 0 asignaciones vigentes (lista vacía)
- [x] 7.3 Triangular test masiva: caso con usuario cuyo rol no existe en el contexto (igual se crea, rol viene del payload)
- [x] 7.4 Ejecutar cobertura: `pytest --cov=app/api/v1/routers/equipos --cov=app/repositories/asignacion_repository` → ≥80%
