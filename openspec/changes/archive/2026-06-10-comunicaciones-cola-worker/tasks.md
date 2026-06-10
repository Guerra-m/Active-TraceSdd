# Tasks — comunicaciones-cola-worker (C-12)

## Task 10.1 — Migration 009: tablas `lotes_comunicacion` + `comunicaciones`
- [x] Crear `backend/alembic/versions/20260610_009_comunicaciones.py`
  - down_revision = "20260610_008"
  - CREATE TABLE lotes_comunicacion (cols según design)
  - CREATE TABLE comunicaciones (cols según design, destinatario TEXT cifrado)
  - Índices necesarios en comunicaciones: (tenant_id, lote_id), (tenant_id, estado), (tenant_id, entrada_padron_id)

## Task 10.2 — Modelos ORM
- [x] Crear `backend/app/models/lote_comunicacion.py` — modelo LoteComunicacion
- [x] Crear `backend/app/models/comunicacion.py` — modelo Comunicacion
- [x] Actualizar `backend/app/models/__init__.py` con ambos modelos

## Task 10.3 — Repositories
- [x] Crear `backend/app/repositories/comunicacion_repository.py`
  - `create_lote()`
  - `get_lote(lote_id) -> LoteComunicacion | None`
  - `list_lotes(limit, offset) -> list[LoteComunicacion]`
  - `create_batch(comunicaciones) -> int`
  - `get_pendientes_despachables(limit=50) -> list[Comunicacion]`
  - `marcar_enviando(comunicacion_id)` / `marcar_enviado(id)` / `marcar_error(id, detalle)`
  - `cancelar_por_lote(lote_id) -> int`

## Task 10.4 — Email sender (integrations)
- [x] Crear `backend/app/integrations/email_sender.py`
  - `AbstractEmailSender` (ABC): `async def send(to, asunto, cuerpo)`
  - `StubSender`: log a logger (no SMTP, usado en dev/test)
  - `get_sender() -> AbstractEmailSender` — fábrica según `settings.email_backend`
- [x] Agregar `email_backend: str = "stub"` a `backend/app/core/config.py`
- [x] Agregar `comunicacion_umbral_aprobacion: int = 10` a settings

## Task 10.5 — Worker
- [x] Crear `backend/app/workers/comunicacion_worker.py`
  - `ComunicacionWorker(db_factory, sender)` con `async def loop()`
  - Obtiene lotes despachables → marca Despachando → procesa mensajes → actualiza contadores
  - Manejo de errores: una falla individual no aborta el lote
- [x] Crear `backend/app/workers/__init__.py`
- [x] Modificar `backend/app/main.py`: en lifespan iniciar `asyncio.create_task(worker.loop())`

## Task 10.6 — Service
- [x] Crear `backend/app/services/comunicacion_service.py`
  - `render_preview(asunto_tpl, cuerpo_tpl, variables) -> tuple[str, str]`
    - Interpola `{{nombre}}`, `{{apellidos}}` con `str.replace()`
  - `crear_lote(asunto_tpl, cuerpo_tpl, destinatarios, materia_id, enviado_por, tenant_id, requiere_aprobacion, db) -> LoteComunicacion`
    - Crea LoteComunicacion
    - Por cada destinatario: descifra email de EntradaPadron, crea Comunicacion renderizada y cifra destinatario
  - `aprobar_lote(lote_id, aprobado_por, tenant_id, db) -> LoteComunicacion`
  - `cancelar_lote(lote_id, tenant_id, db) -> int`

## Task 10.7 — Schemas
- [x] Crear `backend/app/schemas/comunicaciones.py`
  - `PreviewRequest` / `PreviewResponse`
  - `DestinatarioInput(entrada_padron_id, nombre, apellidos)`
  - `CrearLoteRequest` / `LoteComunicacionResponse`

## Task 10.8 — Router
- [x] Crear `backend/app/api/v1/routers/comunicaciones.py`
  - 5 endpoints según API Design del design.md
  - `comunicacion:enviar` para crear/listar/cancelar
  - `comunicacion:aprobar` para aprobar
  - Audit COMUNICACION_ENVIAR en crear_lote
- [x] Registrar en `backend/app/main.py`
- [x] Agregar `COMUNICACION_ENVIAR` a `backend/app/core/audit.py`

## Task 10.9 — Tests
- [x] Crear `backend/tests/test_comunicaciones.py` con ≥6 tests:
  - `test_preview_renderiza_variables` — `{{nombre}}` sustituido correctamente
  - `test_crear_lote_mensajes_pendiente` — lote creado, N mensajes en Pendiente, destinatario cifrado en DB
  - `test_lote_requiere_aprobacion_por_volumen` — si destinatarios > umbral → requiere_aprobacion=True
  - `test_aprobar_lote_cambia_estado` — POST /aprobar → estado lote = Aprobado
  - `test_cancelar_lote_cancela_mensajes` — DELETE → mensajes pasan a Cancelado
  - `test_worker_procesa_pendiente_a_enviado` — worker StubSender procesa un lote → Enviado
