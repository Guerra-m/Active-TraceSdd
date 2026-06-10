## Why

Sin las entidades raíz del dominio académico (Carrera, Cohorte, Materia), ningún módulo posterior puede operar: calificaciones, equipos docentes, encuentros, comunicaciones y coloquios cuelgan de estas entidades. C-06 es el next step del camino crítico y desbloquea C-07 (usuarios y asignaciones). ADR-006 ya está cerrada: Materia es el catálogo único del tenant; la instancia contextual (Dictado = materia × carrera × cohorte) se materializa más adelante cuando los módulos académicos la requieran.

## What Changes

- Modelo `Carrera`: código único por tenant, nombre, estado (Activa/Inactiva). ABM en `/api/v1/admin/carreras` con guard `estructura:gestionar`.
- Modelo `Cohorte`: nombre único por `(tenant_id, carrera_id, nombre)`, año, vigencia `vig_desde/vig_hasta`, estado. ABM en `/api/v1/admin/cohortes`.
- Modelo `Materia`: código único por tenant, nombre, estado. ABM en `/api/v1/admin/materias`. Es el catálogo de referencia; no se duplica por carrera.
- Migración `005_estructura_academica`: crea tablas `carreras`, `cohortes`, `materias` con constraints de unicidad, índices y FK hacia `audit_log.materia_id` (pendiente de C-05).
- Schemas Pydantic de request/response para los tres recursos.
- Tests: CRUD completo, unicidad por tenant, aislamiento multi-tenant, regla de carrera inactiva bloqueando cohorte nueva.

## Capabilities

### New Capabilities

- `carrera-abm`: Modelo ORM `Carrera`, migración 005 (tabla `carreras`), router `/admin/carreras` con GET/POST/PUT/PATCH estado, guard `estructura:gestionar`.
- `cohorte-abm`: Modelo ORM `Cohorte`, tabla `cohortes`, router `/admin/cohortes`, regla carrera-inactiva-bloquea-cohorte.
- `materia-abm`: Modelo ORM `Materia`, tabla `materias`, router `/admin/materias`, FK retroactiva desde `audit_log.materia_id`.

### Modified Capabilities

- `audit-log-model`: se añade la FK de `audit_log.materia_id` → `materias.id` que fue diferida en C-05.

## Impact

- **Nuevos archivos**: `app/models/carrera.py`, `app/models/cohorte.py`, `app/models/materia.py`, `app/repositories/carrera_repository.py`, `app/repositories/cohorte_repository.py`, `app/repositories/materia_repository.py`, `app/schemas/estructura.py`, `app/api/v1/routers/estructura.py`.
- **Migración**: `alembic/versions/20260610_005_estructura_academica.py`.
- **Modificado**: `app/models/__init__.py` (registrar 3 modelos), `app/main.py` (registrar router), `app/core/rbac_seed.py` ya tiene `estructura:gestionar` en ADMIN — sin cambios.
- **Tests**: `tests/test_estructura_academica.py`.
- **Sin cambios en**: auth, RBAC, audit_log (excepto la FK que se añade vía migración).
