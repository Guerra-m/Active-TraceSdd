## 1. Seguridad y Safety Net

- [x] 1.1 Verificar que el permiso `encuentros:gestionar` existe en RBAC seed; agregarlo para PROFESOR, COORDINADOR, ADMIN si falta
- [x] 1.2 Ejecutar test suite baseline: capturar N tests antes de cualquier cambio

## 2. Migración de Base de Datos

- [x] 2.1 Crear `backend/app/models/slot_encuentro.py` — SlotEncuentro (TenantScopedBase): asignacion_id, materia_id, titulo, hora (Time), dia_semana (String check), fecha_inicio (Date), cant_semanas (Integer), fecha_unica (Date nullable), meet_url, vig_desde, vig_hasta
- [x] 2.2 Crear `backend/app/models/instancia_encuentro.py` — InstanciaEncuentro (TenantScopedBase): slot_id (nullable FK), materia_id, fecha (Date), hora (Time), titulo, estado (check: Programado|Realizado|Cancelado), meet_url, video_url, comentario
- [x] 2.3 Crear `backend/app/models/guardia.py` — Guardia (TenantScopedBase): asignacion_id, materia_id, carrera_id, cohorte_id, dia (String check), horario, estado (check: Pendiente|Realizada|Cancelada), comentarios
- [x] 2.4 Registrar los 3 modelos en `backend/app/models/__init__.py`
- [x] 2.5 Crear migración Alembic `20260610_010_encuentros_guardias.py` con las 3 tablas

## 3. Repositories

- [x] 3.1 Crear `SlotEncuentroRepository` con `list_filtrado(materia_id, asignacion_id)`
- [x] 3.2 Crear `InstanciaEncuentroRepository` con `list_filtrado(materia_id, estado, fecha_desde, fecha_hasta)`, `list_para_html(materia_id, asignacion_id)` (no canceladas, orden fecha+hora ASC)
- [x] 3.3 Crear `GuardiaRepository` con `list_filtrado(materia_id, estado, asignacion_id, solo_tenant)` — `solo_tenant=True` devuelve todo, `asignacion_ids` filtra por tutor

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/encuentros.py`: `SlotEncuentroCreate` (valida modos excluyentes, cant_semanas ≤ 52), `InstanciaEncuentroUpdate` (estado, meet_url, video_url, comentario — todos opcionales), `SlotEncuentroResponse`, `InstanciaEncuentroResponse`
- [x] 4.2 Crear `backend/app/schemas/guardias.py`: `GuardiaCreate`, `GuardiaResponse`
- [x] 4.3 Todos con `model_config = ConfigDict(extra='forbid')`

## 5. Service — Generación de instancias

- [x] 5.1 Crear `backend/app/services/encuentro_service.py` con `crear_slot(payload, session, tenant_id, asignacion_id)`:
  - Modo recurrente: crea `SlotEncuentro` + N `InstanciaEncuentro` (fecha_inicio + i×7 días)
  - Modo único: crea solo 1 `InstanciaEncuentro` con `slot_id=NULL`
  - Retorna `(slot_o_none, instancias)`

## 6. Tests — RED primero (TDD)

- [x] 6.1 `test_encuentros.py` — slot recurrente 4 semanas genera 4 instancias (RED)
- [x] 6.2 `test_encuentros.py` — cant_semanas > 52 → 422 (RED)
- [x] 6.3 `test_encuentros.py` — encuentro único: 0 slots, 1 instancia con slot_id=NULL (RED)
- [x] 6.4 `test_encuentros.py` — payload con ambos modos → 422 (RED)
- [x] 6.5 `test_encuentros.py` — PATCH instancia: solo esa instancia cambia (RN-14) (RED)
- [x] 6.6 `test_encuentros.py` — PATCH instancia de otro tenant → 404 (RED)
- [x] 6.7 `test_encuentros.py` — GET /aula-virtual: HTML correcto, canceladas excluidas, orden fecha ASC (RED)
- [x] 6.8 `test_encuentros.py` — GET /admin: COORD ve todos los encuentros del tenant (RED)
- [x] 6.9 `test_encuentros.py` — GET /admin tenant isolation (RED)
- [x] 6.10 `test_guardias.py` — POST guardia: creación exitosa con asignacion_id del JWT (RED)
- [x] 6.11 `test_guardias.py` — GET guardias: TUTOR ve solo las suyas (RED)
- [x] 6.12 `test_guardias.py` — GET guardias: COORD ve todas del tenant (RED)
- [x] 6.13 `test_guardias.py` — GET /exportar: CSV con columnas correctas, tenant isolation (RED)

## 7. Routers — Implementación (GREEN)

- [x] 7.1 Crear `backend/app/api/v1/routers/encuentros.py` con prefijo `/api/v1/encuentros`:
  - `POST /slots` → llama a `EncuentroService.crear_slot`
  - `GET /slots` → listado slots con filtros
  - `GET /` → listado instancias con filtros
  - `PATCH /{id}` → editar instancia
  - `GET /aula-virtual` → bloque HTML (Response con media_type text/html)
  - `GET /admin` → vista transversal COORD/ADMIN
- [x] 7.2 Crear `backend/app/api/v1/routers/guardias.py` con prefijo `/api/v1/guardias`:
  - `POST /` → crear guardia
  - `GET /` → listar (scope por rol)
  - `GET /exportar` → StreamingResponse CSV
- [x] 7.3 Registrar ambos routers en `app/main.py`
- [x] 7.4 Todos los endpoints con `require_permission("encuentros:gestionar")` e identidad del JWT

## 8. Triangulación y Cobertura

- [x] 8.1 Triangular: slot recurrente de 1 semana (caso mínimo) → 1 instancia
- [x] 8.2 Triangular: GET /aula-virtual sin instancias → HTML vacío `<ul></ul>`
- [x] 8.3 Triangular: TUTOR no puede ver guardias de otro TUTOR del mismo tenant
- [x] 8.4 Ejecutar suite completa: `py -m pytest --tb=short -q` → sin regresiones, nuevos tests verdes
