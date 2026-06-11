## MODIFIED Requirements

### Requirement: Router protegido con rutas de coordinación
El sistema SHALL incluir rutas para todas las páginas de coordinación bajo el guard `<RequireAuth>`.

#### Scenario: Rutas de coordinación accesibles con sesión
- **WHEN** un usuario autenticado navega a `/equipos`, `/avisos`, `/tareas`, `/monitor`, `/encuentros/admin`, `/coloquios` o `/setup-cuatrimestre`
- **THEN** el sistema renderiza la página correspondiente dentro del AppLayout

#### Scenario: Ruta de coordinación sin sesión redirige a login
- **WHEN** un usuario no autenticado intenta acceder a `/equipos`
- **THEN** el sistema redirige a `/login`

### Requirement: Menú de navegación con ítems de coordinación
El sistema SHALL mostrar los ítems de coordinación en la sidebar para usuarios con los permisos correspondientes.

#### Scenario: Ítems visibles con permisos
- **WHEN** el usuario tiene `equipos:asignar`, `avisos:publicar`, `tareas:gestionar`, `encuentros:gestionar`, `atrasados:ver`, `coloquios:read`
- **THEN** la sidebar muestra los ítems: Equipos, Avisos, Tareas, Monitor, Encuentros (Admin), Coloquios, Setup Cuatrimestre

#### Scenario: Ítems ocultos sin permisos
- **WHEN** el usuario no tiene los permisos de coordinación
- **THEN** los ítems de coordinación no aparecen en la sidebar
