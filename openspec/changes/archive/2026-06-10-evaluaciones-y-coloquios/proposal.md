# Proposal: evaluaciones-y-coloquios (C-14)

## Qué

Implementar el módulo de coloquios y evaluaciones: modelos `Evaluacion`, `ReservaEvaluacion` y `ResultadoEvaluacion` con sus endpoints REST bajo `/api/v1/coloquios`.

## Por qué

El flujo FL-07 requiere que COORD/ADMIN puedan crear convocatorias de coloquio con cupos, importar alumnos habilitados, y que los ALUMNO reserven su turno. Sin esto, la épica 7 queda bloqueada.

## Scope

- Modelos ORM: `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`
- Migración `20260610_011_evaluaciones_coloquios`
- Permisos nuevos: `coloquios:gestionar` para COORD/ADMIN/PROFESOR
- Schemas Pydantic v2 en `app/schemas/coloquios.py`
- Repository `app/repositories/evaluacion_repository.py`
- Service `app/services/coloquio_service.py` (lógica de cupos)
- Router `app/api/v1/routers/coloquios.py`
- Tests TDD ≥ 2 casos por comportamiento (cupo, reserva, métricas, tenant isolation)

## Out of scope

- Notificaciones por email al alumno al reservar (C-12)
- Integración Moodle para importar candidatos
