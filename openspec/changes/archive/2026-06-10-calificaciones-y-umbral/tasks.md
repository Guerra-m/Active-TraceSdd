## 1. Migración 008 — tablas calificaciones y umbral_materia

- [x] 1.1 Crear `alembic/versions/20260610_008_calificaciones.py` con revision 008, down_revision 007
- [x] 1.2 `CREATE TABLE umbral_materia`: unique `(tenant_id, asignacion_id, materia_id)`; JSONB valores_aprobatorios default `["Satisfactorio","Supera lo esperado"]`
- [x] 1.3 `CREATE TABLE calificaciones`: scope `(asignacion_id, materia_id)`; `entrada_padron_id` nullable (SET NULL); `aprobado` boolean; índices `(tenant_id, asignacion_id, materia_id)`, `(tenant_id, materia_id)`, `(tenant_id, entrada_padron_id)`
- [x] 1.4 Downgrade: DROP TABLE `calificaciones` → DROP TABLE `umbral_materia`

## 2. Modelos ORM

- [x] 2.1 Crear `app/models/umbral_materia.py`: `UmbralMateria(TenantScopedBase, Base)` con `asignacion_id`, `materia_id`, `umbral_pct` (SmallInteger default=60), `valores_aprobatorios` (JSONB); unique constraint
- [x] 2.2 Crear `app/models/calificacion.py`: `Calificacion(TenantScopedBase, Base)` con `asignacion_id`, `materia_id`, `entrada_padron_id` (nullable), `actividad`, `nota_numerica`, `nota_textual`, `aprobado`, `origen`, `importado_at`; índices
- [x] 2.3 Registrar `UmbralMateria` y `Calificacion` en `app/models/__init__.py`

## 3. Repositorios

- [x] 3.1 Crear `app/repositories/umbral_materia_repository.py`: `get_by_asignacion_materia`, `upsert`
- [x] 3.2 Crear `app/repositories/calificacion_repository.py`: `create_batch` (lotes 500), `delete_by_asignacion_materia`, `list_by_asignacion_materia`

## 4. Parser de calificaciones LMS

- [x] 4.1 Crear `app/services/calificacion_parser.py`: detecta columnas `(Real)` → nota_numerica (RN-01); columnas no-metadato → nota_textual; identifica alumno por email; lanza `CalificacionParseError`

## 5. Servicio de importación

- [x] 5.1 Crear `app/services/calificacion_service.py`: mapea filas → busca EntradaPadron por email → calcula `aprobado` con umbral → batch insert; retorna (total, actividades_detectadas)

## 6. Schemas Pydantic

- [x] 6.1 Crear `app/schemas/calificaciones.py`: `ImportarCalificacionesResponse`, `UmbralMateriaRequest`, `UmbralMateriaResponse` (con `es_default`), `CalificacionResponse`

## 7. Router y endpoints

- [x] 7.1 Crear `app/api/v1/routers/calificaciones.py` con `router = APIRouter(prefix="/api/v1", tags=["calificaciones"])`
- [x] 7.2 `POST /calificaciones/importar` (Form: archivo + asignacion_id + materia_id): parsea → busca padrón activo → importa → audit → commit → 201
- [x] 7.3 `DELETE /calificaciones/{asignacion_id}/{materia_id}`: soft-delete por scope asignación × materia → 204 (RN-04)
- [x] 7.4 `GET /calificaciones/umbral/{asignacion_id}/{materia_id}`: retorna umbral o default con es_default=True
- [x] 7.5 `PUT /calificaciones/umbral/{asignacion_id}/{materia_id}`: upsert umbral → 200
- [x] 7.6 Registrar `calificaciones_router` en `app/main.py`

## 8. Tests de integración (TDD)

- [x] 8.1 test_importar_calificaciones_csv_201: CSV con columnas (Real) → 201, filas_importadas=4, actividades detectadas
- [x] 8.2 test_aprobado_calculado_con_umbral: nota=60 → True, nota=59 → False (umbral default 60%, raw DB query)
- [x] 8.3 test_importar_sin_padron_activo_ok: import sin padrón activo → 201, entrada_padron_id=null en DB
- [x] 8.4 test_vaciar_calificaciones_scope_aislado: DELETE vacía solo datos propios de la asignación, no afecta COORDINADOR B misma materia
- [x] 8.5 test_umbral_get_default: GET sin configurar → umbral_pct=60, es_default=True
- [x] 8.6 test_umbral_put_y_get: PUT 75% → GET retorna 75, es_default=False
