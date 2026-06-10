## ADDED Requirements

### Requirement: Resolución de permisos efectivos server-side
El sistema SHALL implementar `RbacService.get_effective_permissions(user_id, tenant_id, db)` que retorna el conjunto de permisos efectivos del usuario como `set[tuple[str, bool]]` donde cada tupla es `(permiso_code, is_own_resource)`. La resolución es SIEMPRE server-side: se consulta DB en cada llamada.

#### Scenario: Usuario con un rol activo obtiene sus permisos
- **WHEN** se llama `get_effective_permissions` para un usuario con rol PROFESOR vigente
- **THEN** el resultado incluye todos los permisos del rol PROFESOR con sus flags `is_own_resource` correctos

#### Scenario: Usuario sin roles activos obtiene set vacío
- **WHEN** se llama `get_effective_permissions` para un usuario sin asignaciones vigentes
- **THEN** el resultado es un set vacío

#### Scenario: Permisos de múltiples roles se unen correctamente
- **WHEN** el usuario tiene roles TUTOR y COORDINADOR ambos vigentes
- **THEN** el resultado contiene la unión de permisos de ambos roles, sin duplicados

#### Scenario: Permiso global prevalece si aparece con ambos flags
- **WHEN** el mismo permiso aparece con `is_own_resource=True` en un rol y `is_own_resource=False` en otro
- **THEN** en el set resultante ese permiso aparece con `is_own_resource=False`

---

### Requirement: Identidad para la resolución viene exclusivamente del JWT
El sistema SHALL obtener `user_id` y `tenant_id` exclusivamente del JWT verificado (vía `get_current_user`). NUNCA de parámetros de request, headers arbitrarios ni body.

#### Scenario: Resolución usa identidad del JWT
- **WHEN** un request incluye un JWT válido para el usuario U del tenant T
- **THEN** `get_effective_permissions` se invoca con los IDs del JWT, ignorando cualquier otro parámetro de la petición

#### Scenario: Token de un tenant no resuelve permisos de otro tenant
- **WHEN** un usuario del tenant A presenta un JWT con `tenant_id=A`
- **THEN** la query de permisos filtra por `tenant_id=A`, nunca cruza datos del tenant B

---

### Requirement: Cache de permisos en el scope del request
El sistema SHALL cachear el resultado de `get_effective_permissions` en `request.state` para la duración del request, evitando queries redundantes si múltiples dependencies invocan la resolución en el mismo request.

#### Scenario: Query de DB se ejecuta una sola vez por request con múltiples guards
- **WHEN** un endpoint declara dos `require_permission` distintos
- **THEN** la query de resolución a DB se ejecuta exactamente una vez por request (el resultado del primero se reutiliza en el segundo)
