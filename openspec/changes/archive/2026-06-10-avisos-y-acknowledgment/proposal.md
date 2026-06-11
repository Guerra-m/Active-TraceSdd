# Proposal: avisos-y-acknowledgment (C-15)

## Qué

Módulo de avisos institucionales con segmentación de audiencia y confirmación de lectura (ack). Incluye ABM de avisos (COORD/ADMIN) y visualización filtrada para cada usuario según su rol y contexto académico.

## Por qué

F3.5 y RN-18/19/20 del dominio. Los avisos son el canal principal de comunicación interna sin salida de email. Sin este módulo, no hay forma de informar a grupos específicos de docentes/alumnos.

## Scope

- Modelos ORM: `Aviso`, `AcknowledgmentAviso`
- Migración `20260610_012_avisos_acknowledgment`
- Schemas Pydantic v2 en `app/schemas/avisos.py`
- Repository `app/repositories/aviso_repository.py`
- Service `app/services/aviso_service.py` (filtrado por scope y vigencia)
- Router `app/api/v1/routers/avisos.py`
- Tests TDD ≥ 2 casos por comportamiento (scope, vigencia, ack, orden)

## Permisos (ya en seed)

- `avisos:publicar` → COORD, ADMIN (ABM avisos)
- `avisos:confirmar` → ALUMNO, TUTOR, PROFESOR, COORD, ADMIN (ack)
