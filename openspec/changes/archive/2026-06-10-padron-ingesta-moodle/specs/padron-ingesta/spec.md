## ADDED Requirements

### Requirement: VersionPadron gestiona versiones de padrón por materia×cohorte con historial conservado
El sistema SHALL implementar `VersionPadron` como entidad que registra una versión del padrón de alumnos para una combinación `(tenant_id, materia_id, cohorte_id)`. Cada importación SHALL crear una nueva `VersionPadron` y desactivar la versión anterior (si existe) en la misma transacción atómica. Solo SHALL existir una versión con `activa=True` por `(tenant_id, materia_id, cohorte_id)` en simultáneo. Las versiones anteriores SHALL conservarse en DB (soft-deactivate, no hard-delete) para auditoría.

#### Scenario: Importar padrón crea nueva versión y desactiva la anterior
- **WHEN** un PROFESOR importa un nuevo padrón para materia M y cohorte C cuando ya existe una versión activa
- **THEN** la versión anterior queda con `activa=False` y la nueva versión queda con `activa=True`; ambas existen en DB

#### Scenario: Primera importación crea versión sin desactivar nada
- **WHEN** un PROFESOR importa un padrón para materia M y cohorte C sin versión previa
- **THEN** el sistema crea la `VersionPadron` con `activa=True` y retorna 201

#### Scenario: Fallo en inserción de entradas hace rollback completo
- **WHEN** la importación falla a mitad de la inserción de entradas (ej.: dato inválido en fila 50)
- **THEN** ninguna entrada nueva ni la nueva versión quedan en DB; la versión anterior permanece activa

---

### Requirement: EntradaPadron registra cada alumno del padrón con PII cifrada
El sistema SHALL implementar `EntradaPadron` con: `version_id` FK → VersionPadron, `tenant_id`, `usuario_id` UUID nullable (alumno puede no tener cuenta), `nombre`, `apellidos`, `email_encrypted` (AES-256-GCM — nunca texto plano en DB), `comision`, `regional`. El campo `usuario_id` SHALL ser null si el alumno aún no tiene cuenta de usuario en el sistema.

#### Scenario: Email de alumno almacenado cifrado en DB
- **WHEN** se importa un padrón con el email "alumno@test.com"
- **THEN** la columna `email_encrypted` en DB contiene un ciphertext AES-GCM (formato `nonce_b64:data_b64`), nunca el texto plano

#### Scenario: Entrada con usuario_id null es válida
- **WHEN** se importa un padrón con un alumno sin cuenta en el sistema
- **THEN** la EntradaPadron se crea con `usuario_id=null` sin error

#### Scenario: Entradas pertenecen al tenant del importador
- **WHEN** un PROFESOR del tenant A importa un padrón
- **THEN** todas las `EntradaPadron` creadas tienen `tenant_id` igual al tenant del PROFESOR

---

### Requirement: Importación desde archivo xlsx/csv vía endpoint POST /api/v1/padron/importar
El sistema SHALL exponer `POST /api/v1/padron/importar` que acepta `multipart/form-data` con: `archivo` (UploadFile .xlsx o .csv), `materia_id` (UUID), `cohorte_id` (UUID). Columnas mínimas requeridas en el archivo: `nombre`, `apellidos`, `email`. Columnas opcionales: `comision`, `regional`. El sistema SHALL detectar columnas por nombre (case-insensitive). El endpoint SHALL requerir permiso `calificaciones:importar` con scope `is_own_resource` para PROFESOR (requiere Asignacion vigente del PROFESOR para esa materia×cohorte), y sin restricción de propio para COORDINADOR/ADMIN.

#### Scenario: PROFESOR importa padrón de su propia asignación — 201
- **WHEN** un PROFESOR con asignación vigente en materia M y cohorte C importa un xlsx válido
- **THEN** el sistema retorna 201 con `version_id`, `filas_importadas`, `materia_id`, `cohorte_id`

#### Scenario: PROFESOR intenta importar padrón de materia sin asignación — 403
- **WHEN** un PROFESOR sin asignación en materia M intenta importar padrón para M
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: COORDINADOR importa padrón de cualquier materia del tenant — 201
- **WHEN** un COORDINADOR importa un xlsx válido para cualquier materia del tenant
- **THEN** el sistema retorna 201

#### Scenario: Archivo con columnas faltantes retorna 422
- **WHEN** se sube un archivo csv que no tiene columna `email`
- **THEN** el sistema retorna 422 Unprocessable Content con detalle de columna faltante

#### Scenario: Import registra PADRON_CARGAR en audit_log
- **WHEN** un PROFESOR importa un padrón exitosamente
- **THEN** el log de auditoría contiene una entrada `PADRON_CARGAR` con actor_id, tenant_id y `filas_importadas` en detalle

---

### Requirement: Vaciar padrón activo con DELETE scope-isolated
El sistema SHALL exponer `DELETE /api/v1/padron/{materia_id}/{cohorte_id}` que marca `activa=False` en la versión activa de esa combinación para el tenant del actor. Requiere permiso `calificaciones:importar`. Para PROFESOR (is_own_resource), SHALL verificar que tenga asignación vigente para esa materia×cohorte. Si no hay versión activa, SHALL retornar 404.

#### Scenario: Vaciar padrón activo retorna 204 y desactiva la versión
- **WHEN** un PROFESOR con asignación vigente llama DELETE para su materia×cohorte
- **THEN** el sistema retorna 204 y la versión queda con `activa=False`

#### Scenario: Vaciar cuando no hay versión activa retorna 404
- **WHEN** un COORDINADOR llama DELETE para una materia×cohorte sin versión activa
- **THEN** el sistema retorna 404

#### Scenario: Aislamiento multi-tenant en vaciar
- **WHEN** un ADMIN del tenant A llama DELETE para una materia del tenant B
- **THEN** el sistema retorna 404 (la materia no existe en el tenant A)
