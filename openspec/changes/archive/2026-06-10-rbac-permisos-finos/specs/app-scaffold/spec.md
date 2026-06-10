## MODIFIED Requirements

### Requirement: Router principal incluye todos los routers activos
El router principal de la API SHALL incluir el router de catálogo RBAC (`/api/v1/rbac`) junto con los routers existentes de auth y health.

#### Scenario: Endpoints RBAC disponibles tras el arranque
- **WHEN** la aplicación arranca con C-04 aplicado
- **THEN** los endpoints GET `/api/v1/rbac/roles` y GET `/api/v1/rbac/roles/{rol_id}/permisos` responden (con autenticación)

#### Scenario: Endpoints existentes no se ven afectados
- **WHEN** se registra el nuevo router RBAC
- **THEN** los endpoints `/api/v1/auth/*` y `/api/v1/health` siguen funcionando sin cambios
