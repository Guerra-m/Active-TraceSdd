## Context

C-04 (RBAC) y C-05 (audit-log) están completos. La plataforma tiene autenticación, autorización por permisos finos y registro de auditoría inmutable. El siguiente paso del camino crítico es C-06: crear las entidades catálogo del dominio académico — Carrera, Cohorte y Materia — sin las cuales ningún módulo posterior (calificaciones, equipos, comunicaciones) puede operar.

ADR-006 está cerrada: Materia es el catálogo global del tenant (no duplica por carrera). El concepto de Dictado (materia × carrera × cohorte = instancia de cursado) se materializa en C-07 o cuando los módulos académicos lo requieran.

**Estado actual**: las tablas `carreras`, `cohortes`, `materias` no existen. `audit_log.materia_id` es un UUID sin FK (diferida en C-05 para evitar dependencia circular).

## Goals / Non-Goals

**Goals:**
- Crear modelos ORM y tablas para Carrera, Cohorte y Materia con aislamiento multi-tenant
- ABM CRUD endpoints bajo `/api/v1/admin/` protegidos con `estructura:gestionar`
- Migración 005 que crea las 3 tablas y añade la FK diferida `audit_log.materia_id → materias.id`
- Regla de negocio: carrera Inactiva no admite creación de nuevas cohortes
- Tests de integración con DB real (sin mocks)

**Non-Goals:**
- Dictado / instancia de cursado (materia × carrera × cohorte) — viene después
- Inscripción de alumnos a cohortes o materias
- Calificaciones, equipos docentes, encuentros
- Importación masiva desde CSV o Moodle
- Paginación avanzada de listas (lista simple es suficiente aquí)

## Decisions

### 1. TenantScopedBase para los tres modelos
Los tres modelos heredan de `TenantScopedBase`, que inyecta `id (UUID PK)`, `tenant_id (FK tenants)`, `created_at`, `updated_at` y soft delete via `deleted_at`. Alineado con la regla dura de soft delete + multi-tenancy row-level.

Alternativa considerada: heredar de `Base` sin soft delete. Rechazada — auditoría append-only es contrato de plataforma.

### 2. Materia es catálogo plano del tenant (ADR-006)
Una materia tiene `(tenant_id, codigo)` único. No existe una materia-por-carrera; la asociación contextual (dictado) se crea en C-07 o posterior.

Alternativa considerada: materia anidada bajo carrera. Rechazada — duplica el catálogo; ADR-006 cierra la discusión.

### 3. Permiso único `estructura:gestionar` cubre las 3 entidades
Los tres routers usan `Depends(require_permission("estructura:gestionar"))`. El seed ya asigna este permiso a ADMIN (migración 003). No se crean permisos separados por entidad en esta fase.

Alternativa: permisos `carrera:gestionar`, `cohorte:gestionar`, `materia:gestionar`. Rechazada — sobre-ingeniería prematura; se puede granularizar si aparece un caso de uso real.

### 4. Estado enum como `String` con check constraint
`estado` en Carrera y Materia es `VARCHAR(20)` con `CheckConstraint("estado IN ('Activa', 'Inactiva')")`, no un `Enum` SQL nativo. Razón: los enums nativos de PostgreSQL son costosos de alterar (requieren downtime); el check constraint es equivalente en validación y más flexible.

### 5. Cohorte usa vig_desde/vig_hasta sin enum de estado
Cohorte no tiene campo `estado` explícito. Una cohorte está "activa" si `vig_hasta IS NULL OR vig_hasta >= hoy`. Si se necesita inactivación manual en el futuro, se añade. La carrera padre es quien porta el estado `Activa/Inactiva`.

Alternativa: campo `estado` igual que Carrera/Materia. Diferida — la KB habla de vigencia temporal, no de estado discreto, y el dominio es menos maduro aquí.

### 6. FK diferida audit_log.materia_id añadida en migración 005
En C-05 se guardó `materia_id` como UUID sin FK para evitar que la migración 004 dependa de la tabla `materias`. La migración 005 añade el constraint `ALTER TABLE audit_log ADD CONSTRAINT fk_audit_materia FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE SET NULL`.

`ON DELETE SET NULL` es la única opción segura dado que audit_log es inmutable (trigger impide UPDATE/DELETE de filas, pero si se borra la materia via soft-delete la FK no se viola porque soft delete no borra la fila).

Nota: el trigger de inmutabilidad del audit_log impide UPDATE en `materia_id`. El FK solo asegura integridad referencial en inserts. Si se quiere referenciar una materia soft-deleted, el UUID seguirá siendo válido porque la fila de materias permanece (soft delete).

### 7. Repositorios con scope tenant automático
`CarreraRepository`, `CohorteRepository`, `MateriaRepository` filtran por `tenant_id` en todos los métodos de lectura. Los métodos de escritura fuerzan `tenant_id` desde el token (no desde el body).

### 8. Endpoints bajo `/api/v1/admin/`
Prefix `/admin/` señaliza semánticamente que estas rutas son solo para ADMIN. No hay lógica adicional; el guard `estructura:gestionar` es el mecanismo de control.

## Risks / Trade-offs

- **Cohorte sin estado explícito**: si el dominio requiere "archivar" una cohorte sin que expire, habrá que añadir el campo luego. → Mitigación: la migración es incremental; añadir `estado` a `cohortes` es una migración sencilla en el futuro.
- **FK audit_log → materias ON DELETE SET NULL**: aunque audit_log es inmutable, la FK actúa solo en INSERT. Si el modelo de datos cambia y se usa hard delete (prohibido por las reglas duras), los registros de audit quedarían sin referencia. → Mitigación: las reglas duras impiden hard delete; si se viola, el FK falla antes de llegar al trigger.
- **PA-01 abierta sobre Dictado**: la relación Dictado no está aquí pero C-07 (usuarios:asignaciones) puede necesitarla. → Mitigación: C-07 es el siguiente change; se evaluará si Dictado debe crearse en C-06b o en C-07 directamente.

## Migration Plan

1. Aplicar migración 005 con `alembic upgrade head` (en local y en test)
2. Las 3 tablas nuevas: sin datos existentes, sin riesgo de migración de datos
3. La FK diferida en `audit_log.materia_id`: `ALTER TABLE audit_log ADD CONSTRAINT ...` — operación rápida en tabla vacía en desarrollo, en prod puede requerir CONCURRENTLY si la tabla es grande
4. Rollback: `alembic downgrade -1` elimina las 3 tablas y el constraint FK (en orden inverso: FK primero, tablas después)
