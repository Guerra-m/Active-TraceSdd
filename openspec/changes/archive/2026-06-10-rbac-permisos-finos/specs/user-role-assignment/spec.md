## ADDED Requirements

### Requirement: Asignación de roles a usuarios con vigencia temporal
El sistema SHALL mantener una tabla `usuario_rol` que asigna uno o más roles a un usuario dentro de un tenant, con vigencia temporal explícita. Cada fila tiene `user_id` (FK), `rol_id` (FK), `tenant_id`, `valid_from DATE NOT NULL`, `valid_until DATE` (nullable = vigencia abierta), `created_at`, `updated_at`, `deleted_at`. La combinación `(user_id, rol_id, tenant_id, valid_from)` es UNIQUE para evitar duplicados.

#### Scenario: Asignación de rol con vigencia abierta
- **WHEN** se crea una fila `usuario_rol` con `valid_from=hoy` y `valid_until=NULL`
- **THEN** el usuario ejerce los permisos del rol indefinidamente hasta que se establezca `valid_until`

#### Scenario: Asignación vencida no otorga acceso
- **WHEN** existe una fila `usuario_rol` con `valid_until` en el pasado
- **THEN** esa asignación NO se incluye en la resolución de permisos efectivos del usuario

#### Scenario: Asignación futura no otorga acceso todavía
- **WHEN** existe una fila `usuario_rol` con `valid_from` en el futuro
- **THEN** esa asignación NO se incluye en la resolución de permisos efectivos del usuario hasta que llegue la fecha

#### Scenario: Histórico de asignaciones se conserva
- **WHEN** se vence una asignación (se establece `valid_until` en el pasado)
- **THEN** la fila persiste en DB con sus fechas originales (NO se borra físicamente ni se hace soft delete)

---

### Requirement: Un usuario puede tener múltiples roles simultáneos
El sistema SHALL permitir que un usuario tenga más de un rol vigente al mismo tiempo. Los permisos efectivos son la unión de todos los roles vigentes.

#### Scenario: Unión de permisos de múltiples roles
- **WHEN** un usuario tiene roles TUTOR y COORDINADOR ambos vigentes
- **THEN** sus permisos efectivos incluyen TODOS los permisos de ambos roles

#### Scenario: Un permiso global prevalece sobre el mismo permiso con is_own_resource
- **WHEN** un usuario tiene dos asignaciones del mismo permiso `calificaciones:importar`, una con `is_own_resource=True` (via PROFESOR) y otra con `is_own_resource=False` (via COORDINADOR)
- **THEN** el permiso efectivo es `is_own_resource=False` (acceso global prevalece sobre restricto)

---

### Requirement: Scope de tenant en asignaciones
El sistema SHALL garantizar que las asignaciones de roles son siempre tenant-specific: un usuario de tenant A no puede tener roles del tenant B, y la consulta de asignaciones siempre filtra por el tenant del usuario autenticado.

#### Scenario: Aislamiento de asignaciones entre tenants
- **WHEN** el usuario autenticado de tenant A consulta sus permisos efectivos
- **THEN** solo se consideran asignaciones con `tenant_id` del tenant A, nunca de otro tenant
