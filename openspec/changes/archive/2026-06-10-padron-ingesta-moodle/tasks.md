## 1. Migración 007 — tablas version_padron y entrada_padron

- [x] 1.1 Crear `alembic/versions/20260610_007_padron.py` con revision 007, down_revision 006
- [x] 1.2 `CREATE TABLE version_padron`: `id UUID PK`, `tenant_id FK tenants`, `materia_id FK materias`, `cohorte_id FK cohortes`, `cargado_por FK users`, `cargado_at TIMESTAMPTZ NOT NULL`, `activa BOOLEAN NOT NULL DEFAULT TRUE`; índice `(tenant_id, materia_id, cohorte_id)`; índice `(tenant_id, materia_id, cohorte_id, activa)`
- [x] 1.3 `CREATE TABLE entrada_padron`: `id UUID PK`, `version_id FK version_padron`, `tenant_id FK tenants`, `usuario_id FK users nullable`, `nombre VARCHAR(200) NOT NULL`, `apellidos VARCHAR(200) NOT NULL`, `email_encrypted TEXT NOT NULL`, `comision VARCHAR(100)`, `regional VARCHAR(100)`; índice `(tenant_id, version_id)`; índice `(tenant_id, usuario_id)`
- [x] 1.4 Downgrade: DROP TABLE `entrada_padron` → DROP TABLE `version_padron` (en ese orden)

## 2. Modelos ORM

- [x] 2.1 Crear `app/models/version_padron.py`: clase `VersionPadron(TenantScopedBase, Base)` con columnas `materia_id`, `cohorte_id`, `cargado_por`, `cargado_at`, `activa`; índices compuestos
- [x] 2.2 Crear `app/models/entrada_padron.py`: clase `EntradaPadron(TenantScopedBase, Base)` con columnas `version_id`, `usuario_id` (nullable), `nombre`, `apellidos`, `email_encrypted`, `comision`, `regional`
- [x] 2.3 Registrar `VersionPadron` y `EntradaPadron` en `app/models/__init__.py`

## 3. Repositorios

- [x] 3.1 Crear `app/repositories/version_padron_repository.py`: métodos `get_activa(materia_id, cohorte_id)`, `desactivar(version)`, `create`; scope tenant obligatorio
- [x] 3.2 Crear `app/repositories/entrada_padron_repository.py`: métodos `create_batch(entradas: list[EntradaPadron])` (flush en lotes de 500), `list_by_version(version_id)`; scope tenant obligatorio

## 4. Parser de archivos

- [x] 4.1 Crear `app/services/padron_parser.py`: función `parse_padron_file(contents: bytes, filename: str) -> list[dict]` que detecta xlsx vs csv por extensión; para csv intenta utf-8 con fallback latin-1; normaliza nombres de columna a lowercase; valida columnas mínimas (`nombre`, `apellidos`, `email`); lanza `PadronParseError` con detalle de columna faltante o fila inválida

## 5. Integración Moodle WS

- [x] 5.1 Crear `app/integrations/moodle_ws.py`: clases `MoodleNotConfiguredError`, `MoodleWSError(status_code, retry_after)`, `MoodleWSClient` con `httpx.AsyncClient`; método `get_course_participants(course_id) -> list[dict]`; timeout 30s desde `Settings.MOODLE_TIMEOUT` (default 30); lanza `MoodleWSError` en errores HTTP >= 500 o de red; lanza `MoodleNotConfiguredError` si `MOODLE_URL` vacío
- [x] 5.2 Agregar `MOODLE_URL: str = ""` y `MOODLE_TOKEN: str = ""` y `MOODLE_TIMEOUT: int = 30` a `app/core/config.py` (`Settings`)

## 6. Schemas Pydantic

- [x] 6.1 Crear `app/schemas/padron.py`: `ImportarPadronResponse` (version_id, filas_importadas, materia_id, cohorte_id); `EntradaPadronResponse` (id, nombre, apellidos, comision, regional — SIN email en respuesta estándar); `SyncMoodleRequest` (materia_id, cohorte_id, moodle_course_id opcional); todos con `extra='forbid'`

## 7. Router y endpoints

- [x] 7.1 Crear `app/api/v1/routers/padron.py` con `router = APIRouter(prefix="/api/v1", tags=["padron"])`
- [x] 7.2 Implementar `POST /padron/importar` (`UploadFile` + `materia_id` + `cohorte_id` como Form fields): parsea archivo → crea nueva VersionPadron → desactiva anterior → inserta EntradaPadron en batch → audit PADRON_CARGAR → commit → 201 con `ImportarPadronResponse`; verifica asignación vigente del PROFESOR (is_own_resource) o COORDINADOR/ADMIN sin verificación
- [x] 7.3 Implementar `DELETE /padron/{materia_id}/{cohorte_id}`: obtiene versión activa → la desactiva → audit → commit → 204; 404 si no hay versión activa; verifica asignación propia del PROFESOR
- [x] 7.4 Implementar `POST /padron/sync-moodle`: construye `MoodleWSClient` → llama `get_course_participants` → mapea a formato padron → reutiliza lógica de importación (misma transacción, mismo audit); maneja `MoodleNotConfiguredError` → 422; maneja `MoodleWSError` → 502 con `retry_after`
- [x] 7.5 Registrar `padron_router` en `app/main.py`

## 8. Tests de integración (TDD)

- [x] 8.1 test_importar_csv_201: archivo CSV válido → 201, filas_importadas=2, version_id en respuesta
- [x] 8.2 test_email_cifrado_en_db: tras importar, email_encrypted en DB es ciphertext AES-GCM (contiene ':'), no es el plaintext
- [x] 8.3 test_reimportar_desactiva_version_anterior: segunda importación desactiva la primera versión (versionado D1)
- [x] 8.4 test_profesor_sin_asignacion_403: PROFESOR con padron:importar (is_own_resource=True) pero sin asignación vigente → 403
- [x] 8.5 test_aislamiento_multi_tenant: admin_b no puede desactivar versión activa del padrón de tenant_a → 404
- [x] 8.6 test_sync_moodle_no_configurado_422: POST /padron/sync-moodle sin MOODLE_URL/TOKEN → 422
