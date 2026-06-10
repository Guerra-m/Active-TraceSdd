## 1. Migración 005 — estructura académica

- [x] 1.1 Crear `alembic/versions/20260610_005_estructura_academica.py` con tablas `carreras`, `cohortes`, `materias` y FK diferida `audit_log.materia_id → materias.id ON DELETE SET NULL`
- [x] 1.2 Tabla `carreras`: columnas `(id UUID PK, tenant_id FK, codigo VARCHAR(50), nombre VARCHAR(200), estado VARCHAR(20) CHECK IN('Activa','Inactiva') DEFAULT 'Activa', deleted_at, created_at, updated_at)` + UniqueConstraint(`tenant_id`, `codigo`)
- [x] 1.3 Tabla `cohortes`: columnas `(id UUID PK, tenant_id FK, carrera_id FK carreras.id, nombre VARCHAR(100), anio SMALLINT, vig_desde DATE NOT NULL, vig_hasta DATE nullable, deleted_at, created_at, updated_at)` + UniqueConstraint(`tenant_id`, `carrera_id`, `nombre`)
- [x] 1.4 Tabla `materias`: columnas `(id UUID PK, tenant_id FK, codigo VARCHAR(50), nombre VARCHAR(200), estado VARCHAR(20) CHECK IN('Activa','Inactiva') DEFAULT 'Activa', deleted_at, created_at, updated_at)` + UniqueConstraint(`tenant_id`, `codigo`)
- [x] 1.5 `ALTER TABLE audit_log ADD CONSTRAINT fk_audit_materia FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE SET NULL` en el upgrade; `DROP CONSTRAINT` en el downgrade

## 2. Modelos ORM

- [x] 2.1 Crear `app/models/carrera.py`: clase `Carrera(TenantScopedBase)` con columnas de la migración
- [x] 2.2 Crear `app/models/cohorte.py`: clase `Cohorte(TenantScopedBase)` con FK a `carreras.id`
- [x] 2.3 Crear `app/models/materia.py`: clase `Materia(TenantScopedBase)` con columnas de la migración
- [x] 2.4 Registrar los tres modelos en `app/models/__init__.py` (imports + `__all__`)

## 3. Repositorios

- [x] 3.1 Crear `app/repositories/carrera_repository.py`: métodos `get_by_id`, `list_by_tenant`, `create`, `update_estado`, `soft_delete`; scope `tenant_id` en todas las lecturas
- [x] 3.2 Crear `app/repositories/cohorte_repository.py`: métodos `get_by_id`, `list_by_tenant`, `create`, `soft_delete`; scope `tenant_id` en todas las lecturas
- [x] 3.3 Crear `app/repositories/materia_repository.py`: métodos `get_by_id`, `list_by_tenant`, `create`, `update_estado`, `soft_delete`; scope `tenant_id` en todas las lecturas

## 4. Schemas Pydantic

- [x] 4.1 Crear `app/schemas/estructura.py` con schemas request/response para Carrera: `CarreraCreate`, `CarreraResponse`, `CarreraEstadoUpdate`; todos con `extra='forbid'`
- [x] 4.2 Agregar schemas de Cohorte al mismo archivo: `CohorteCreate`, `CohorteResponse`; `extra='forbid'`
- [x] 4.3 Agregar schemas de Materia: `MateriaCreate`, `MateriaResponse`, `MateriaEstadoUpdate`; `extra='forbid'`

## 5. Routers y endpoints

- [x] 5.1 Crear `app/api/v1/routers/estructura.py` con `router = APIRouter(prefix="/api/v1/admin", tags=["estructura-academica"])`
- [x] 5.2 Implementar endpoints de Carrera: `GET /carreras`, `POST /carreras`, `GET /carreras/{id}`, `PUT /carreras/{id}`, `PATCH /carreras/{id}/estado`, `DELETE /carreras/{id}`; todos con `Depends(require_permission("estructura:gestionar"))`
- [x] 5.3 Implementar endpoints de Cohorte: `GET /cohortes`, `POST /cohortes`, `GET /cohortes/{id}`, `DELETE /cohortes/{id}`; misma guard; POST valida que `carrera.estado == "Activa"` antes de crear
- [x] 5.4 Implementar endpoints de Materia: `GET /materias`, `POST /materias`, `GET /materias/{id}`, `PUT /materias/{id}`, `PATCH /materias/{id}/estado`, `DELETE /materias/{id}`; misma guard
- [x] 5.5 Registrar el router en `app/main.py`

## 6. Tests de integración (TDD)

- [x] 6.1 Crear `backend/tests/test_estructura_academica.py` con fixtures de tenant y usuario ADMIN
- [x] 6.2 Tests Carrera: crear exitoso (201), código duplicado (409), aislamiento multi-tenant, ADMIN puede listar, TUTOR recibe 403
- [x] 6.3 Tests Cohorte: crear exitosa (201), nombre duplicado (409), carrera inactiva bloquea cohorte (422), carrera de otro tenant da 404, cohortes existentes visibles tras inactivar carrera
- [x] 6.4 Tests Materia: crear exitosa (201), código duplicado (409), aislamiento multi-tenant, ALUMNO recibe 403, PATCH estado Inactiva (200), PATCH estado inválido (422)
- [x] 6.5 Test FK audit_log.materia_id: insertar audit_log con `materia_id` válido y con NULL; verificar que soft-delete de materia no rompe FK de audit_log existente
