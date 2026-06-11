# Tasks: programas-y-fechas-academicas (C-17)

## Implementación

- [x] Crear modelo `FechaAcademica` con tipo, numero, periodo, fecha, titulo (materia_id × cohorte_id)
- [x] Crear modelo `ProgramaMateria` con referencia_archivo opaca (materia_id × carrera_id × cohorte_id)
- [x] Registrar modelos en `app/models/__init__.py`
- [x] Migración Alembic `20260610_014_programas_fechas.py` (down_revision = 013)
- [x] Schemas Pydantic v2 con `extra='forbid'` en `app/schemas/programas.py`
- [x] `FechaAcademicaRepository` con `list_filtrado(materia_id, cohorte_id, periodo, tipo)` ordenado por fecha ASC
- [x] `ProgramaMateriaRepository` con `list_filtrado(materia_id, carrera_id, cohorte_id)`
- [x] Router `programas_router` (POST/GET/DELETE `/api/v1/programas`) — permiso `estructura:gestionar`
- [x] Router `fechas_router` (POST/GET/PATCH/DELETE `/api/v1/fechas-academicas`) — permiso `estructura:gestionar`
- [x] Registrar ambos routers en `app/main.py`
- [x] Agregar `estructura:gestionar` a COORDINADOR en `rbac_seed.py`
- [x] Tests TDD: CRUD programas, filtrado por materia, CRUD fechas, filtrado por periodo, editar, soft-delete, tenant isolation (8 tests, todos ✅)
