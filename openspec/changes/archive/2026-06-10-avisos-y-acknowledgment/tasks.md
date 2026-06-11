# Tasks: avisos-y-acknowledgment (C-15)

## Bloque 1 — Modelos ORM

- [x] 1.1 Crear `backend/app/models/aviso.py` con `Aviso` y `AcknowledgmentAviso`
- [x] 1.2 Registrar en `backend/app/models/__init__.py`

## Bloque 2 — Migración

- [x] 2.1 Crear `backend/alembic/versions/20260610_012_avisos_acknowledgment.py`

## Bloque 3 — Schemas

- [x] 3.1 Crear `backend/app/schemas/avisos.py`

## Bloque 4 — Repository + Service

- [x] 4.1 Crear `backend/app/repositories/aviso_repository.py`
- [x] 4.2 Crear `backend/app/services/aviso_service.py` (filtrado scope + vigencia)

## Bloque 5 — Router

- [x] 5.1 Crear `backend/app/api/v1/routers/avisos.py`
- [x] 5.2 Registrar en `backend/app/main.py`

## Bloque 6 — Tests TDD

- [x] 6.1 RED: crear aviso Global y verlo
- [x] 6.2 TRIANGULATE: aviso PorRol — solo lo ve el rol correcto
- [x] 6.3 RED: aviso fuera de vigencia no aparece
- [x] 6.4 TRIANGULATE: aviso sin fin_en siempre vigente
- [x] 6.5 RED: ack registra confirmación
- [x] 6.6 TRIANGULATE: aviso con requiere_ack ya ack-eado no aparece en lista
- [x] 6.7 RED: orden de prioridad
- [x] 6.8 TRIANGULATE: aviso PorMateria solo lo ve usuario con asignacion en esa materia
