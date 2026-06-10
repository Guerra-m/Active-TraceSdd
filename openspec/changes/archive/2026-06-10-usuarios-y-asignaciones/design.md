## Context

El modelo `User` creado en C-02 contiene únicamente los campos de autenticación: `email_encrypted`, `email_hash`, `password_hash`, `is_active`, `totp_*`. C-07 agrega el perfil de identidad docente (PII) y la entidad de asignación contextual que relaciona un docente con un rol académico en un período.

**Governance CRÍTICO**: cualquier error aquí compromete privacidad (PII expuesta), seguridad (vigencia de permisos) o integridad financiera (liquidaciones y facturación). Cada decisión de diseño debe ser explícita y auditable.

## Goals / Non-Goals

**Goals:**
- Extender `users` con campos de perfil PII cifrados (AES-256): dni, cuil, cbu, alias_cbu; más datos no-PII: nombre, apellidos, banco, regional, legajo, facturador, estado.
- Crear entidad `Asignacion`: usuario ↔ rol en contexto académico (materia/carrera/cohorte) con vigencia temporal y jerarquía responsable.
- ABM `/api/v1/admin/usuarios` (guard `usuarios:gestionar`) y `/api/v1/asignaciones` (guard `equipos:asignar`).
- `estado_vigencia` derivado en runtime: nunca persistido, siempre calculado.
- Tests que prueban que PII nunca aparece en texto plano en DB ni en respuestas de API.

**Non-Goals:**
- Asignación masiva (bulk) — viene en C-08 equipos-docentes.
- Clonar equipo entre períodos — C-08.
- Login/refresh/recuperación de password — ya en C-02/C-03.
- Perfil del alumno (ALUMNO es un rol asignado; no tiene entidad propia en esta fase).
- Grilla salarial y liquidaciones — C-18.

## Decisions

### 1. Extender `users` en lugar de crear tabla separada de perfil
La alternativa era `perfil_docente` separado con FK a `users`. Rechazada: introduce JOIN obligatorio en todo contexto donde se necesite nombre o legajo, complica el RBAC (dos entidades para "un usuario"), y el modelo de dominio trata al usuario como unidad única.

Alternativa 2: tabla independiente `docentes` sin herencia de User. Rechazada: duplica gestión de identidad; el usuario ya existe en auth desde C-02.

**Decisión**: `ALTER TABLE users ADD COLUMN nombre ...` en migración 006. El modelo ORM actualizado refleja los campos nuevos. Los campos de auth existentes no se tocan. Los campos nuevos son nullable en DB (para filas auth-only pre-C-07) pero los routers de C-07 los exigen en create.

### 2. Campos PII cifrados individualmente (no block-cipher del registro)
Cifrar cada campo PII por separado con AES-256 permite búsquedas por hash y descifrado selectivo (no hay que descifrar todo el registro para leer el nombre).

Patrón ya establecido en C-02 con `email_encrypted` + `email_hash`. C-07 sigue el mismo patrón para dni, cuil, cbu, alias_cbu:
- `dni_encrypted`: AES-256 del DNI en texto plano.
- `dni_hash`: SHA-256 normalizado — permite búsqueda por DNI sin exponer el valor (uso futuro).
- Igual para cuil, cbu, alias_cbu (sin hash de búsqueda para cbu/alias_cbu — su uso es operativo, no lookup).

### 3. `email` no se duplica — ya existe en `users`
`email_encrypted` y `email_hash` están desde C-02. C-07 no añade una segunda columna de email. La unicidad por `(tenant_id, email_hash)` ya la garantiza el índice único de auth.

### 4. `estado` de dominio vs `is_active` de auth
`is_active` controla si el usuario puede autenticarse (flag de auth). `estado` (Activo/Inactivo) es el estado de dominio del perfil docente. Ambos coexisten:
- `is_active=False` → no puede loguear.
- `estado='Inactivo'` → no se muestra en equipos, no recibe asignaciones nuevas, pero sus registros históricos existen.
- Soft delete de User: `deleted_at` del TenantScopedBase.

### 5. `Asignacion` usa `comisiones` como JSONB array
Las comisiones son strings libres (identificadores de división interna). Usar JSONB evita una tabla pivot `asignacion_comision` que añadiría complejidad sin beneficio en esta fase. Si en el futuro se requieren queries por comisión, se añade un índice GIN sobre el JSONB.

### 6. `estado_vigencia` derivado — nunca columna en DB
Se calcula en runtime: `"Vigente" if (hoy >= desde) and (hasta is None or hoy <= hasta) else "Vencida"`. Persistirlo crearía stale data y requeriría un job de actualización. El cálculo es O(1) y sin overhead relevante.

### 7. PII nunca en respuestas estándar de API
Los schemas de respuesta (`UsuarioResponse`) no incluyen dni, cuil, cbu, alias_cbu. Existe un endpoint separado `GET /api/v1/admin/usuarios/{id}/pii` con guard adicional (mismo permiso + logging de audit) para cuando ADMIN necesita ver PII completa. Esto minimiza la superficie de exposición.

### 8. `equipos:asignar` ya existe en el seed RBAC — sin nuevos permisos
El seed de C-04 tiene `equipos:asignar` (COORDINADOR, ADMIN) y `usuarios:gestionar` (ADMIN). C-07 reutiliza estos permisos. No se añaden permisos nuevos en esta fase.

### 9. Migración 006 — ALTER TABLE nullable primero, NOT NULL luego
Para evitar table lock en producción al agregar columnas NOT NULL con valores default, la migración 006 añade las columnas PII como nullable. Si en el futuro se requieren NOT NULL, una segunda migración puede agregar el constraint tras backfill. En desarrollo con DB vacía esto no aplica, pero es el patrón correcto.

## Risks / Trade-offs

- **[Riesgo] PII visible en logs de SQLAlchemy (echo=True)** → Mitigación: `echo=False` en producción (ya configurado en Settings). Los tests usan `echo=False`. Los campos PII nunca se loguean explícitamente.
- **[Riesgo] DNI/CUIL descifrados accidentalmente en repr() del modelo** → Mitigación: `__repr__` de `User` no incluye campos PII cifrados; solo `id` y `tenant_id`.
- **[Riesgo] ALTER TABLE users lenta en producción (tabla grande)** → Mitigación: En PostgreSQL, ADD COLUMN nullable es O(1) (solo metadata). Sin DEFAULT calculado en servidor, sin rewrite de tabla.
- **[Riesgo] `comisiones` JSONB sin validación de esquema** → Mitigación: Pydantic valida `list[str]` antes de persistir; el JSONB almacena el array validado.
- **[Riesgo] PA-08 abierta: semántica de NEXO** → Mitigación: NEXO puede asignarse (el modelo lo permite); los permisos de NEXO son vacíos en el seed base. C-07 no bloquea ni asume comportamiento de NEXO.

## Migration Plan

1. Migración 006 upgrade: `ALTER TABLE users ADD COLUMN nombre ...` (nullable) + `CREATE TABLE asignaciones`.
2. Rollback (downgrade): `DROP TABLE asignaciones` + `ALTER TABLE users DROP COLUMN nombre, DROP COLUMN apellidos, ...`.
3. En producción: upgrade en ventana de mantenimiento (ALTER TABLE nullable es instantáneo en PG).
4. Sin migración de datos existentes (no hay filas de usuario con perfil antes de C-07).

## Open Questions

- **ADR-008 (NEXO)**: ¿Puede un NEXO gestionar asignaciones? ¿Tiene contexto de materia? La decisión del modelo no requiere respuesta ahora — el campo `rol` en `Asignacion` acepta 'NEXO' y el sistema no restringe. Los permisos de NEXO son vacíos en el seed; una extensión posterior los rellena.
- **Búsqueda por DNI**: ¿Habrá un lookup por DNI en esta fase? Si no, no hace falta `dni_hash`. Por ahora se incluye solo `dni_encrypted` (sin hash). Se puede añadir el hash en C-07b si aparece el caso de uso.
