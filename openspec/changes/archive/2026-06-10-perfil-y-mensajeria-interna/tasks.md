# Tasks: perfil-y-mensajeria-interna (C-20)

## Implementación

- [x] Agregar permisos `perfil:editar` e `inbox:usar` en rbac_seed.py (todos los roles)
- [x] Modelo `HiloMensaje` (asunto, remitente_id, destinatario_id)
- [x] Modelo `MensajeInterno` (hilo_id, autor_id, cuerpo)
- [x] Registrar modelos en `app/models/__init__.py`
- [x] Migración Alembic `20260610_015_perfil_mensajeria.py` (hilos_mensaje, mensajes_internos)
- [x] Schemas Pydantic v2 en `app/schemas/perfil.py`: PerfilResponse, PerfilUpdate, HiloMensajeCreate/Response, MensajeInternoCreate/Response
- [x] `HiloMensajeRepository.list_para_usuario(user_id)` — WHERE remitente=uid OR destinatario=uid, ORDER BY created_at DESC
- [x] `MensajeInternoRepository.list_by_hilo(hilo_id)` — ORDER BY created_at ASC
- [x] Router `GET/PUT /api/v1/perfil` — usa UserRepository.update_perfil; CUIL excluido del schema de PUT
- [x] Router `GET/POST /api/v1/inbox` — listar hilos propios; crear hilo con primer mensaje
- [x] Router `GET/POST /api/v1/inbox/{id}` — leer/responder hilo; 403 si usuario no es participante
- [x] Registrar router en `app/main.py`
- [x] Tests TDD (9 tests): get_perfil, CUIL solo lectura, update campos editables, update parcial, crear hilo, lista hilos propios, responder hilo (orden ASC), tercero 403, tenant isolation ✅
