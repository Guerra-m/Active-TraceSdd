## 1. Migración 006 — extensión users + tabla asignaciones

- [x] 1.1 Crear `alembic/versions/20260610_006_usuarios_asignaciones.py` con revision 006, down_revision 005
- [x] 1.2 `ALTER TABLE users ADD COLUMN`: `nombre VARCHAR(200)`, `apellidos VARCHAR(200)`, `dni_encrypted TEXT`, `cuil_encrypted TEXT`, `cbu_encrypted TEXT`, `alias_cbu_encrypted TEXT`, `banco VARCHAR(100)`, `regional VARCHAR(100)`, `legajo VARCHAR(50)`, `legajo_profesional VARCHAR(50)`, `facturador BOOLEAN DEFAULT FALSE`, `estado VARCHAR(20) CHECK IN('Activo','Inactivo') DEFAULT 'Activo'` — todas nullable en DB
- [x] 1.3 Crear tabla `asignaciones`: `id UUID PK`, `tenant_id FK tenants`, `usuario_id FK users`, `rol VARCHAR(20) CHECK IN('ALUMNO','TUTOR','PROFESOR','COORDINADOR','NEXO','ADMIN','FINANZAS')`, `materia_id UUID FK materias nullable`, `carrera_id UUID FK carreras nullable`, `cohorte_id UUID FK cohortes nullable`, `comisiones JSONB DEFAULT '[]'`, `responsable_id UUID FK users nullable`, `desde DATE NOT NULL`, `hasta DATE nullable`, `deleted_at`, `created_at`, `updated_at`
- [x] 1.4 Índices en `asignaciones`: `(tenant_id)`, `(tenant_id, usuario_id)`, `(tenant_id, materia_id)`, `(tenant_id, rol)`
- [x] 1.5 Downgrade: `DROP TABLE asignaciones` + `ALTER TABLE users DROP COLUMN nombre, apellidos, dni_encrypted, cuil_encrypted, cbu_encrypted, alias_cbu_encrypted, banco, regional, legajo, legajo_profesional, facturador, estado`

## 2. Modelo ORM — User extendido y Asignacion

- [x] 2.1 Actualizar `app/models/user.py`: agregar columnas de perfil (`nombre`, `apellidos`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `estado`); actualizar `__repr__` para NO incluir campos PII
- [x] 2.2 Crear `app/models/asignacion.py`: clase `Asignacion(TenantScopedBase, Base)` con columnas de la migración; propiedad Python `estado_vigencia` calculada (`@property`)
- [x] 2.3 Registrar `Asignacion` en `app/models/__init__.py`

## 3. Repositorios

- [x] 3.1 Extender `app/repositories/user_repository.py`: agregar `create_usuario(...)` con cifrado AES-256 de PII, `update_perfil(id, ...)`, `find_by_email_hash` ya existe
- [x] 3.2 Crear `app/repositories/asignacion_repository.py`: métodos `get_by_id`, `list_by_tenant(filtros opcionales: usuario_id, rol, materia_id, carrera_id, cohorte_id)`, `create`, `update`, `soft_delete`; scope tenant en todos; `estado_vigencia` inyectado desde `@property` del modelo

## 4. Schemas Pydantic

- [x] 4.1 Crear `app/schemas/usuarios.py`: `UsuarioCreate` (con campos PII en texto plano para recepción), `UsuarioUpdate`, `UsuarioResponse` (SIN dni/cuil/cbu/alias_cbu), `UsuarioPIIResponse` (CON campos PII desencriptados — solo para endpoint dedicado); todos con `extra='forbid'`
- [x] 4.2 Crear `app/schemas/asignaciones.py`: `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` (incluye `estado_vigencia` derivado); `extra='forbid'`

## 5. Routers y endpoints

- [x] 5.1 Crear `app/api/v1/routers/usuarios.py` con `router = APIRouter(prefix="/api/v1/admin", tags=["usuarios"])`
- [x] 5.2 Endpoints de usuarios: `GET /usuarios`, `POST /usuarios`, `GET /usuarios/{id}`, `PUT /usuarios/{id}`, `DELETE /usuarios/{id}`; todos con `Depends(require_permission("usuarios:gestionar"))`
- [x] 5.3 Endpoint PII: `GET /usuarios/{id}/pii` con mismo guard + registro en `audit_log` (`USUARIO_VER_PII`); retorna `UsuarioPIIResponse` con campos descifrados
- [x] 5.4 Crear `app/api/v1/routers/asignaciones.py` con `router = APIRouter(prefix="/api/v1", tags=["asignaciones"])`
- [x] 5.5 Endpoints de asignaciones: `GET /asignaciones`, `POST /asignaciones`, `GET /asignaciones/{id}`, `PUT /asignaciones/{id}`, `DELETE /asignaciones/{id}`; todos con `Depends(require_permission("equipos:asignar"))`; GET lista soporta query params `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`
- [x] 5.6 Registrar ambos routers en `app/main.py`

## 6. Tests de integración (TDD)

- [x] 6.1 Crear `backend/tests/test_usuarios.py` con fixtures de tenant y ADMIN
- [x] 6.2 Tests Usuario: crear exitoso (201), email duplicado (409), PII cifrada en DB (query raw), respuesta sin PII sensible, COORDINADOR recibe 403, aislamiento multi-tenant, soft delete (204 + desaparece del listado)
- [x] 6.3 Tests endpoint PII `GET /usuarios/{id}/pii`: ADMIN accede y recibe PII desencriptada, registro en audit_log
- [x] 6.4 Crear `backend/tests/test_asignaciones.py` con fixtures de tenant, usuarios y contexto académico
- [x] 6.5 Tests Asignación: crear exitosa (201) con `estado_vigencia=Vigente`, asignación vencida tiene `estado_vigencia=Vencida`, materia de otro tenant da 404, responsable de otro tenant da 404, PROFESOR recibe 403, aislamiento multi-tenant, filtros funcionales (por rol, por materia_id)
- [x] 6.6 Test vigencia: asignación con `hasta=ayer` devuelve `estado_vigencia=Vencida`; asignación con `hasta=null` devuelve `Vigente`
