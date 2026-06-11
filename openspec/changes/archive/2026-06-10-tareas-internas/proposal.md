# Proposal: tareas-internas (C-16)

## Qué

Módulo de tareas internas de coordinación: alta, asignación a docentes, cambio de estado y hilo de comentarios. Alto uso: cientos de tareas simultáneas en período activo.

## Scope

- Modelos ORM: `Tarea`, `ComentarioTarea`
- Migración `20260610_013_tareas_internas`
- Schemas Pydantic v2 en `app/schemas/tareas.py`
- Repository `app/repositories/tarea_repository.py`
- Router `app/api/v1/routers/tareas.py`
- Tests TDD ≥ 2 casos por comportamiento

## Permisos (ya en seed)

- `tareas:gestionar` → PROFESOR/TUTOR (is_own=True), COORDINADOR/ADMIN (is_own=False)
