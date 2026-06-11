# Tasks: panel-auditoria-metricas (C-19)

## Implementación

- [x] `AuditLogQueryRepository` (solo-lectura) con `list_filtrado`, `acciones_por_dia`, `por_actor_materia`
- [x] Schemas Pydantic v2 en `app/schemas/auditoria.py`: AuditLogEntry, AccionPorDia, InteraccionPorActor, MetricasAuditoria
- [x] Router `app/api/v1/routers/auditoria.py` con prefijo `/api/v1/auditoria`
  - GET `` — log filtrado con limit (default 200)
  - GET `/metricas` — métricas agregadas (acciones/día, por actor×materia)
  - Scoping: COORDINADOR (is_own=True) → fuerza actor_id=current_user.id; ADMIN → all tenant
- [x] Registrar router en `app/main.py`
- [x] Tests TDD (7 tests): admin ve todo, filtro por accion, limit configurable, coord solo ve propio, métricas acciones/día, por actor×materia, tenant isolation ✅
