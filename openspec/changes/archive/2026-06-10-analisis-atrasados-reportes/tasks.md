# Tasks — analisis-atrasados-reportes (C-11)

## Task 9.1 — Migration 009: RBAC seed `atrasados:ver`
- [x] `atrasados:ver` ya estaba en migración 003 y en `rbac_seed.py` (TUTOR/PROFESOR/COORDINADOR/ADMIN). Sin migration nueva necesaria.

## Task 9.2 — Service `analisis_service.py`
- [x] Creado `backend/app/services/analisis_service.py`
  - `get_atrasados` → query JOIN + lógica Python para faltantes/reprobadas
  - `get_ranking` → SQL GROUP BY + HAVING + ORDER BY
  - `get_notas_finales` → SQL AVG(nota_numerica) GROUP BY alumno

## Task 9.3 — Schemas `analisis.py`
- [x] Creado `backend/app/schemas/analisis.py`
  - `AlumnoAtrasadoResponse`, `AtrasadosResponse`
  - `AlumnoRankingResponse`, `RankingResponse`
  - `AlumnoNotaFinalResponse`, `NotasFinalesResponse`

## Task 9.4 — Router `analisis.py`
- [x] Creado `backend/app/api/v1/routers/analisis.py`
  - 3 endpoints GET con `_check_asignacion_scope` + `_PERM`

## Task 9.5 — Registro en main.py
- [x] `analisis_router` registrado en `create_app()`

## Task 9.6 — Tests `test_analisis.py`
- [x] Creado `backend/tests/test_analisis.py` con 6 tests:
  - `test_atrasados_detecta_reprobados`
  - `test_atrasados_detecta_faltantes`
  - `test_atrasados_alumno_al_dia_no_aparece`
  - `test_ranking_excluye_sin_aprobadas`
  - `test_ranking_orden_desc`
  - `test_notas_finales_promedio`
