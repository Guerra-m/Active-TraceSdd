## Context

C-03 (auth-jwt-2fa) entregó autenticación completa con JWT de vida corta, refresh rotation, 2FA TOTP y la dependency `get_current_user` que resuelve identidad y tenant exclusivamente desde el token verificado. Los archivos `core/permissions.py` y el slot `require_permission` en `core/dependencies.py` están reservados y vacíos.

El sistema tiene 7 roles de dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) documentados en `knowledge-base/03_actores_y_roles.md §3.3` con una matriz de 19 capacidades. Ningún endpoint de negocio existe aún (C-05 en adelante), por lo que este change establece la infraestructura de autorización sin necesidad de migrar endpoints existentes.

Governance: **CRÍTICO**. El mecanismo de autorización es fundacional — un bug aquí rompe el aislamiento multi-tenant y el modelo de seguridad de todo el sistema.

## Goals / Non-Goals

**Goals:**
- Tablas `roles`, `permisos`, `rol_permiso`, `usuario_rol` como catálogo administrable en DB (no hardcode).
- Migración 003 con seed de los 7 roles del dominio y la matriz base de permisos.
- `RbacService` que resuelve permisos efectivos server-side por request (unión de roles vigentes acotada por tenant).
- Dependency `require_permission("modulo:accion")` implementada; fail-closed → 403 sin permiso explícito.
- Endpoints de catálogo (GET-only) para que ADMIN pueda consultar roles y permisos disponibles.
- Tests completos: usuario sin permiso → 403, unión de roles, permiso `(propio)`, vigencia caducada.

**Non-Goals:**
- Interfaz de administración frontend (es C-21+).
- Endpoints de creación/modificación de roles personalizados por tenant (fase posterior).
- Integración con el audit log (C-05 lo registrará cuando exista).
- Permisos a nivel de objeto (row-level object ACL) — el `(propio)` se maneja como flag en el permiso, no como ACL de fila.
- Caché distribuida de permisos (Redis) — la resolución es DB-backed con query optimizado.

## Decisions

### D1 — Catálogo en BD, no enum en código

**Decisión**: Los roles y permisos se almacenan en tablas `roles` y `permisos`. La matriz `rol_permiso` es una tabla de unión. El seed de los 7 roles y sus permisos vive en la migración 003. Los endpoints posteriores solo referencian permisos por su `code` string (`modulo:accion`).

**Alternativa descartada**: Enum Python `class Permission(str, Enum)` con checks `in`. Hardcodear la matriz impide administración por tenant y requiere deploy para cualquier ajuste de permisos.

**Rationale**: La KB establece explícitamente que la matriz rol × permiso debe ser un catálogo administrable como datos, no código. Permite que cada tenant personalice sus roles en el futuro sin cambios de código.

---

### D2 — `is_own_resource` flag en `RolPermiso`, no permiso separado

**Decisión**: La tabla `rol_permiso` tiene una columna booleana `is_own_resource` (default `False`). Cuando es `True`, el permiso `modulo:accion` solo aplica sobre recursos propios del usuario. El guard `require_permission` puede consultar este flag para que el Service layer valide la propiedad del recurso.

**Alternativa descartada**: Dos permisos distintos — `calificaciones:importar` y `calificaciones:importar:propio`. Duplica el catálogo y complica la matrix de seed.

**Alternativa descartada**: Resolución de `(propio)` puramente en el Service. Sin información del flag en la capa de permisos, el guard no puede informar al service si el contexto es "propio" o "global".

**Rationale**: El flag en `rol_permiso` es un metadato de la asignación, no del permiso en sí. Permite que el mismo permiso `calificaciones:importar` sea "propio" para PROFESOR y "global" para COORDINADOR, sin duplicar el catálogo de permisos.

---

### D3 — `UsuarioRol` con vigencia temporal explícita

**Decisión**: `usuario_rol` tiene `valid_from DATE NOT NULL` y `valid_until DATE` (nullable = vigencia abierta). La resolución de permisos efectivos filtra `valid_from <= today <= valid_until OR valid_until IS NULL`. Las asignaciones vencidas se conservan (soft delete no aplica aquí — la vigencia es el mecanismo de expiración).

**Alternativa descartada**: `deleted_at` para "revocar" roles. Impide distinguir entre "asignación planificada futura" (`valid_from` en el futuro) y "asignación revocada". La vigencia temporal es la semántica correcta para rotación de docentes entre cuatrimestres.

**Rationale**: KB §5 especifica que las asignaciones tienen rango `desde/hasta` y que el histórico se conserva. La vigencia explícita satisface ambos requisitos.

---

### D4 — Resolución de permisos en `RbacService`, no en el guard directamente

**Decisión**: `require_permission(code: str)` es una closure FastAPI que retorna una dependency. La dependency llama a `RbacService.get_effective_permissions(user, db)` (que hace la query a DB) y verifica si `code` está en el set resultante.

**Alternativa descartada**: Incluir roles en el JWT claim y resolver permisos en memoria sin DB. El JWT ya lleva `roles` (lista de role codes) del C-03. Pero: (a) cambios de roles no se reflejarían hasta el próximo login; (b) `is_own_resource` no puede viajar en el JWT sin complejidad excesiva.

**Rationale**: La resolución server-side en cada request garantiza que los cambios de roles/permisos son efectivos de inmediato. El costo de la query se mitiga con una query SQL eficiente con JOIN indexado (ver D5).

---

### D5 — Query de resolución con JOIN indexado, resultado cacheado por request

**Decisión**: La query de permisos efectivos es un JOIN `usuario_rol → rol_permiso → permisos` filtrado por `tenant_id`, `user_id` y vigencia. El resultado es un `set[tuple[str, bool]]` (code, is_own_resource) cacheado en el objeto `request.state` durante la vida del request (no entre requests).

**Alternativa descartada**: Redis como caché de permisos cross-request. Introduce infraestructura adicional en esta fase; la invalidación es compleja y no hay suficiente carga para justificarlo en C-04.

**Rationale**: Un solo query por request con JOIN indexado es suficiente para el volumen esperado. El cache de request evita múltiples queries si hay varios `require_permission` en el mismo endpoint (raro, pero posible).

---

### D6 — `roles` y `permisos` NO heredan `TenantScopedBase`; `usuario_rol` y `rol_permiso` SÍ

**Decisión**:
- `Rol` y `Permiso` heredan `Base` directamente (sin `TenantScopedBase`). Llevan `tenant_id` explícita (nullable inicialmente para los roles seed globales), más `is_system` flag para distinguir roles del dominio (no modificables) de roles custom por tenant.
- `RolPermiso` y `UsuarioRol` heredan `TenantScopedBase` — pertenecen al tenant.

**Alternativa descartada**: Todos heredan `TenantScopedBase`. Los roles seed (ALUMNO, TUTOR…) son compartidos entre todos los tenants en la fase inicial; forzarles un `tenant_id` NOT NULL requeriría duplicarlos por tenant en el seed.

**Rationale**: Los roles del dominio (`is_system=True`) son plantillas globales que cada tenant puede extender con roles custom. La separación entre "definición global" y "asignación tenant-specific" es la línea correcta.

---

### D7 — `require_permission` como decorator de endpoint, no middleware

**Decisión**: Se implementa como dependency FastAPI (`Depends(require_permission("calificaciones:importar"))`), no como middleware global ni como decorator de función.

**Alternativa descartada**: Middleware que lee una metadata annotation del endpoint. Requiere instrospección de rutas en runtime, frágil y difícil de testar unitariamente.

**Rationale**: La dependency FastAPI es idiomática, testeable (se puede reemplazar en tests), y permite al endpoint declarar su permiso de forma explícita y visible en el código.

## Risks / Trade-offs

- **[Riesgo] Query de permisos sin índices → degradación bajo carga** → Migración 003 crea índices compuestos en `usuario_rol(user_id, tenant_id, valid_from, valid_until)` y `rol_permiso(rol_id, tenant_id)`.

- **[Riesgo] Seed incorrecto de la matriz** → La migración 003 usa INSERT explícito con valores auditables. Los tests de integración verifican que los 7 roles tienen exactamente los permisos definidos en la KB §3.3.

- **[Riesgo] `is_own_resource` ignorado en el Service layer** → El guard expone el flag en el contexto de la dependency; la ausencia de validación de propiedad en el service es un bug que debe detectarse en code review. Los tests de "permiso propio vs global" cubren este escenario.

- **[Trade-off] Resolución de permisos con DB query por request** → Sin caché cross-request. Para el volumen inicial de activia-trace (decenas de usuarios concurrentes), es aceptable. Si el profiling muestra bottleneck, se añade Redis sin cambiar la interfaz de `RbacService`.

- **[Trade-off] Roles seed marcados `is_system=True` no modificables** → Los roles del dominio no pueden renombrarse ni eliminarse desde la API. Esta restricción simplifica la integridad del seed y el razonamiento sobre el sistema; los tenants pueden crear roles custom adicionales.

## Migration Plan

1. Asegurar que C-03 está completamente aplicado (`alembic current` apunta a revisión `002`).
2. Aplicar migración 003: `alembic upgrade head` — crea tablas + índices + seed de roles y permisos.
3. Verificar seed con `SELECT count(*) FROM roles` (7 filas), `SELECT count(*) FROM permisos` (≥19 filas), `SELECT count(*) FROM rol_permiso`.
4. **Rollback**: `alembic downgrade -1` borra las 4 tablas de C-04. Sin datos de negocio aún, es seguro.

## Open Questions

- ¿El JWT de C-03 ya incluye un claim `roles` con los codes de los roles del usuario, o solo `user_id` y `tenant_id`? Si no lleva roles, `get_current_user` debe enriquecerse (o `RbacService` hace la query completa cada vez). **Decisión necesaria antes de codear D4.**
- ¿El seed de roles debe incluir el rol `NEXO`? La KB lo lista en §2 pero la matriz §3.3 no tiene columna para NEXO. Se asume que NEXO existe como rol sin permisos predefinidos (catálogo vacío, para ser configurado por tenant). Confirmar con el equipo de producto.
