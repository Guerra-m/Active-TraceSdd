## ADDED Requirements

### Requirement: Proyecto frontend scaffolded con stack canónico
El sistema SHALL disponer de un proyecto frontend en `frontend/` con Vite 5, React 18, TypeScript strict, Tailwind CSS, TanStack Query v5, React Hook Form + Zod y Axios. La estructura SHALL seguir el patrón feature-based: `src/features/{name}/{components,hooks,services,types,pages}`. El directorio compartido SHALL estar en `src/shared/`.

#### Scenario: Proyecto arranca en desarrollo sin errores
- **WHEN** se ejecuta `npm run dev` en `frontend/`
- **THEN** Vite inicia el servidor en el puerto 5173 y la consola no muestra errores de compilación TypeScript

#### Scenario: Build de producción genera artefactos estáticos
- **WHEN** se ejecuta `npm run build`
- **THEN** se genera `dist/` con `index.html` y assets hasheados sin errores de TypeScript

#### Scenario: Vitest ejecuta el suite inicial sin fallos
- **WHEN** se ejecuta `npm run test`
- **THEN** todos los tests del setup inicial pasan (≥1 test de smoke de la app)

### Requirement: Layout principal con sidebar y topbar adaptado por permisos
El sistema SHALL renderizar un layout con sidebar de navegación y topbar con datos del usuario autenticado. El menú del sidebar SHALL mostrar únicamente las secciones a las que el usuario tiene al menos un permiso. Los ítems de menú SHALL mapearse a permisos específicos declarados en la configuración del router.

#### Scenario: Usuario con permiso `atrasados:ver` ve la sección de alumnos
- **WHEN** un usuario autenticado con permiso `atrasados:ver` accede a cualquier ruta protegida
- **THEN** el sidebar muestra el ítem "Alumnos / Comisiones" habilitado

#### Scenario: Usuario sin permisos de coordinación no ve esa sección
- **WHEN** un usuario autenticado sin ningún permiso de `equipos:*` accede al layout
- **THEN** el sidebar no muestra el ítem "Coordinación"

#### Scenario: Topbar muestra nombre y rol del usuario
- **WHEN** el usuario está autenticado
- **THEN** el topbar muestra el nombre completo y el rol principal del usuario activo

### Requirement: Contenedor Docker para frontend
El sistema SHALL incluir un `Dockerfile` multi-stage en `frontend/`: etapa `build` (Node 20 Alpine, `npm ci && npm run build`) y etapa `serve` (Nginx Alpine, sirve `dist/`, proxy `/api` al servicio backend). El `docker-compose.yml` raíz SHALL agregar el servicio `frontend` con `build: ./frontend` y puerto `3000:80`.

#### Scenario: Imagen Docker se construye sin errores
- **WHEN** se ejecuta `docker build -t trace-frontend ./frontend`
- **THEN** la imagen se construye sin errores y la etapa final pesa menos de 50 MB

#### Scenario: Nginx en producción sirve la SPA correctamente
- **WHEN** el contenedor arranca y se hace `GET /` a `localhost:3000`
- **THEN** se devuelve `index.html` con status 200

#### Scenario: Rutas de SPA no devuelven 404
- **WHEN** se hace `GET /dashboard` (ruta de la SPA) en producción
- **THEN** Nginx devuelve `index.html` (fallback) con status 200
