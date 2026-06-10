## Architecture

```
Router (comunicaciones.py)
  ├── POST /comunicaciones/preview       → ComunicacionService.render_preview()
  ├── POST /comunicaciones/lotes         → ComunicacionService.crear_lote()
  ├── POST /lotes/{lote_id}/aprobar      → ComunicacionService.aprobar_lote()
  ├── DELETE /lotes/{lote_id}            → ComunicacionService.cancelar_lote()
  └── GET  /comunicaciones/lotes         → ComunicacionRepository.list_lotes()

ComunicacionService (comunicacion_service.py)
  ├── render_preview(asunto, cuerpo, variables) → string
  ├── crear_lote(asunto_tpl, cuerpo_tpl, destinatarios, ...) → LoteComunicacion
  ├── aprobar_lote(lote_id) → LoteComunicacion
  └── cancelar_lote(lote_id) → int (canceladas)

ComunicacionRepository (comunicacion_repository.py)
  ├── create_lote() / get_lote() / list_lotes()
  └── create_batch() / get_pendientes() / marcar_enviando() / marcar_resultado()

ComunicacionWorker (workers/comunicacion_worker.py)
  ├── loop() — asyncio background task, pollea cada poll_interval_s
  └── _despachar(comunicacion) — descifra, llama sender, marca estado

EmailSender (integrations/email_sender.py)
  ├── StubSender — log output (dev/test)
  └── SmtpSender — real SMTP (prod, configurado por env)
```

## Models

### `lotes_comunicacion`
```python
class LoteComunicacion(TenantScopedBase, Base):
    __tablename__ = "lotes_comunicacion"
    enviado_por       = Column(UUID, FK(users.id, RESTRICT), nullable=False)
    materia_id        = Column(UUID, FK(materias.id, RESTRICT), nullable=True)
    asunto_template   = Column(Text, nullable=False)
    cuerpo_template   = Column(Text, nullable=False)
    estado            = Column(String(20), nullable=False, default="Pendiente")
    requiere_aprobacion = Column(Boolean, nullable=False, default=False)
    aprobado_por      = Column(UUID, FK(users.id, RESTRICT), nullable=True)
    aprobado_at       = Column(DateTime(tz=True), nullable=True)
    total_mensajes    = Column(Integer, nullable=False, default=0)
    enviados          = Column(Integer, nullable=False, default=0)
    errores           = Column(Integer, nullable=False, default=0)
```

Estados del lote: `Pendiente | PendienteAprobacion | Aprobado | Despachando | Completado | Cancelado`

### `comunicaciones`
```python
class Comunicacion(TenantScopedBase, Base):
    __tablename__ = "comunicaciones"
    lote_id           = Column(UUID, FK(lotes_comunicacion.id, CASCADE), nullable=False)
    enviado_por       = Column(UUID, FK(users.id, RESTRICT), nullable=False)
    materia_id        = Column(UUID, FK(materias.id, RESTRICT), nullable=True)
    destinatario      = Column(Text, nullable=False)   # cifrado AES-256-GCM
    asunto            = Column(String(500), nullable=False)   # renderizado
    cuerpo            = Column(Text, nullable=False)   # renderizado
    estado            = Column(String(20), nullable=False, default="Pendiente")
    enviado_at        = Column(DateTime(tz=True), nullable=True)
    entrada_padron_id = Column(UUID, FK(entrada_padron.id, SET NULL), nullable=True)
```

Estados del mensaje: `Pendiente | Enviando | Enviado | Error | Cancelado` (RN-15)

## State Machine

```
LoteComunicacion:
  Pendiente          → worker puede despachar si !requiere_aprobacion
  PendienteAprobacion→ espera PATCH /aprobar del coordinador
  Aprobado           → worker puede despachar
  Despachando        → worker lo está procesando (lock)
  Completado         → todos los mensajes en estado final
  Cancelado          → mensajes Pendiente → Cancelado

Comunicacion (RN-15):
  Pendiente  → Enviando (worker lo toma)
  Enviando   → Enviado (SMTP OK)
  Enviando   → Error (SMTP fail)
  Pendiente  → Cancelado (lote cancelado)
```

## API Design

```
POST /api/v1/comunicaciones/preview
  body: {asunto_template, cuerpo_template, variables_ejemplo: {nombre, apellidos}}
  → {asunto_renderizado, cuerpo_renderizado}

POST /api/v1/comunicaciones/lotes
  body: {materia_id?, asunto_template, cuerpo_template,
         destinatarios: [{entrada_padron_id, nombre, apellidos}]}
  → LoteComunicacionResponse (con estado, requiere_aprobacion, total_mensajes)

POST /api/v1/comunicaciones/lotes/{lote_id}/aprobar
  permiso: comunicacion:aprobar
  → LoteComunicacionResponse

DELETE /api/v1/comunicaciones/lotes/{lote_id}
  permiso: comunicacion:enviar (o aprobar)
  → 204

GET /api/v1/comunicaciones/lotes
  permiso: comunicacion:enviar
  → list[LoteComunicacionResponse]
```

## Worker Design

```python
async def loop():
    while True:
        # 1. Obtener lotes despachables (Pendiente+!req_aprobacion O Aprobado)
        # 2. Marcar lote Despachando
        # 3. Para cada Comunicacion Pendiente del lote:
        #    a. marcar Enviando
        #    b. descifrar destinatario
        #    c. sender.send(to, asunto, cuerpo)
        #    d. marcar Enviado o Error
        # 4. Actualizar contadores del lote
        # 5. Si todos terminaron → Completado
        await asyncio.sleep(poll_interval_s)
```

## Migration

`20260610_009_comunicaciones.py`:
- CREATE TABLE `lotes_comunicacion`
- CREATE TABLE `comunicaciones`
- Seed: permisos `comunicacion:enviar` y `comunicacion:aprobar` ya existen en migración 003
- Índices: `(tenant_id, lote_id)`, `(tenant_id, estado)` en comunicaciones
