## ADDED Requirements

### Requirement: Cliente Moodle WS async con fallback a importación manual
El sistema SHALL proveer un módulo `app/integrations/moodle_ws.py` con `MoodleWSClient` que usa `httpx.AsyncClient` para consumir la API estándar de Moodle Web Services. La URL base y el token se leen de `Settings` (`MOODLE_URL`, `MOODLE_TOKEN`). Si `MOODLE_URL` está vacío o no configurado, el cliente SHALL lanzar `MoodleNotConfiguredError`, y el router SHALL responder 422 indicando que se use importación manual por archivo. Los errores de red o HTTP >= 500 de Moodle SHALL traducirse a `MoodleWSError` con código 502 y campo `retry_after=60`.

#### Scenario: Sync on-demand con Moodle WS configurado retorna lista de participantes
- **WHEN** un COORDINADOR llama POST /api/v1/padron/sync-moodle con materia_id y cohorte_id válidos, y MOODLE_URL está configurado
- **THEN** el sistema obtiene participantes de Moodle WS y los importa como nueva VersionPadron, retornando 201

#### Scenario: Sync con Moodle no configurado retorna 422
- **WHEN** MOODLE_URL no está configurado y se llama POST /api/v1/padron/sync-moodle
- **THEN** el sistema retorna 422 con mensaje indicando que se use importación manual

#### Scenario: Error de red de Moodle mapea a 502
- **WHEN** Moodle WS devuelve un error de red o HTTP 500 durante la sincronización
- **THEN** el sistema retorna 502 con `detail` describiendo el error y `retry_after: 60`

---

### Requirement: Sync on-demand protegida con permiso calificaciones:importar
El endpoint `POST /api/v1/padron/sync-moodle` SHALL requerir permiso `calificaciones:importar`. Para PROFESOR SHALL verificar asignación vigente en la materia×cohorte solicitada (is_own_resource). Para COORDINADOR/ADMIN SHALL aplicar sin restricción de propio.

#### Scenario: PROFESOR sin asignación en la materia recibe 403 en sync Moodle
- **WHEN** un PROFESOR sin asignación vigente en materia M intenta sincronizar desde Moodle para M
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: COORDINADOR puede sincronizar cualquier materia del tenant
- **WHEN** un COORDINADOR llama sync-moodle para cualquier materia del tenant con Moodle configurado
- **THEN** el sistema procesa la sincronización sin verificar asignación propia
