## Why

Con Carrera, Cohorte y Materia establecidos (C-06), el siguiente eslabón del camino crítico es la identidad del cuerpo docente y su contexto académico. Sin `Usuario` (perfil completo con PII) y `Asignación` (quién enseña qué, dónde y cuándo), no pueden existir calificaciones, equipos, encuentros, guardias, liquidaciones ni comunicaciones. C-07 desbloquea el gran fork paralelo de FASE 4 (C-08 a C-14).

## What Changes

- **Extensión del modelo `User` existente** (tabla `users`): nuevos campos de perfil y PII (`nombre`, `apellidos`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `estado`). El email ya está cifrado (C-02); no se duplica.
- **Nuevo modelo `Asignacion`**: usuario ↔ rol ↔ contexto académico (`materia_id`, `carrera_id`, `cohorte_id`, `comisiones` JSONB), con `responsable_id` (jerarquía docente), vigencia `desde/hasta` y `estado_vigencia` derivado.
- **Migración 006**: `ALTER TABLE users ADD COLUMN ...`; nueva tabla `asignaciones`.
- **Extensión `UserRepository`**: búsqueda por nombre/apellido, PII desencriptada solo cuando sea necesario (en endpoints explícitos), hash de búsqueda para email ya existente.
- **Nuevo `AsignacionRepository`**: filtros por rol, materia, carrera, cohorte, responsable; cálculo inline de `estado_vigencia` (vigente si `hoy >= desde AND (hasta IS NULL OR hoy <= hasta)`).
- **Schemas Pydantic** (usuarios y asignaciones): respuestas sin PII sensible por defecto; endpoint específico para editar PII con guard adicional.
- **Routers**: `/api/v1/admin/usuarios` (guard `usuarios:gestionar`, ADMIN) y `/api/v1/asignaciones` (guard `equipos:asignar`, COORDINADOR/ADMIN).
- **Tests**: PII nunca en texto plano en DB ni respuestas, unicidad email por tenant, vigencia (vencida no autoriza), multi-rol, jerarquía responsable, aislamiento multi-tenant.

## Capabilities

### New Capabilities

- `usuario-perfil`: extensión de tabla `users` con campos de perfil PII (AES-256) y datos de facturación; ABM en `/api/v1/admin/usuarios`.
- `asignacion-abm`: modelo `Asignacion` con contexto académico y vigencia temporal; ABM + filtros en `/api/v1/asignaciones`; `estado_vigencia` derivado en cada consulta.

### Modified Capabilities

- `user-auth` (`users` table): columnas nuevas añadidas por migración 006; ningún comportamiento auth existente cambia.

## Impact

- **Migración**: `alembic/versions/20260610_006_usuarios_asignaciones.py` — ALTER TABLE users + CREATE TABLE asignaciones.
- **Modificado**: `app/models/user.py` (nuevas columnas), `app/repositories/user_repository.py` (métodos de perfil), `app/models/__init__.py`, `app/main.py`.
- **Nuevos archivos**: `app/models/asignacion.py`, `app/repositories/asignacion_repository.py`, `app/schemas/usuarios.py`, `app/schemas/asignaciones.py`, `app/api/v1/routers/usuarios.py`, `app/api/v1/routers/asignaciones.py`.
- **Tests**: `tests/test_usuarios.py`, `tests/test_asignaciones.py`.
- **Governance CRÍTICO**: PII cifrada, RBAC de identidad. Ningún campo PII en texto plano, ningún log, ninguna respuesta sin hashing/cifrado.
