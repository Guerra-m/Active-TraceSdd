# Tasks: evaluaciones-y-coloquios (C-14)

## Bloque 1 — RBAC seed

- [x] 1.1 Agregar permiso `coloquios:gestionar` al seed de permisos
- [x] 1.2 Agregar entradas de matriz: PROFESOR (is_own=True), COORDINADOR (is_own=False), ADMIN (is_own=False)

## Bloque 2 — Modelos ORM

- [x] 2.1 Crear `backend/app/models/evaluacion.py` con clases `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`
- [x] 2.2 Registrar los tres modelos en `backend/app/models/__init__.py`

## Bloque 3 — Migración

- [x] 3.1 Crear `backend/alembic/versions/20260610_011_evaluaciones_coloquios.py`

## Bloque 4 — Schemas

- [x] 4.1 Crear `backend/app/schemas/coloquios.py` con schemas Create/Response para Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, y schema de métricas

## Bloque 5 — Repository

- [x] 5.1 Crear `backend/app/repositories/evaluacion_repository.py` con `EvaluacionRepository`

## Bloque 6 — Service

- [x] 6.1 Crear `backend/app/services/coloquio_service.py` con lógica de cupos y métricas

## Bloque 7 — Router

- [x] 7.1 Crear `backend/app/api/v1/routers/coloquios.py` con todos los endpoints
- [x] 7.2 Registrar router en `backend/app/main.py`

## Bloque 8 — Tests TDD

- [x] 8.1 RED: test crear convocatoria (COORD)
- [x] 8.2 GREEN: implementación mínima
- [x] 8.3 TRIANGULATE: crear con tipo=Parcial (distinto tipo)
- [x] 8.4 RED: test reservar turno con cupo disponible
- [x] 8.5 GREEN: implementación reserva
- [x] 8.6 TRIANGULATE: reservar sin cupo → 422
- [x] 8.7 RED: test importar alumnos (crear convocados)
- [x] 8.8 GREEN+TRIANGULATE (idempotencia)
- [x] 8.9 RED: test métricas (convocados/reservas/libres)
- [x] 8.10 GREEN+TRIANGULATE (tenant vacío = ceros)
- [x] 8.11 RED: test tenant isolation
- [x] 8.12 GREEN+TRIANGULATE (ALUMNO de otro tenant → 404)
- [x] 8.13 RED: test registro de resultado
- [x] 8.14 GREEN+TRIANGULATE (upsert nota_final)
