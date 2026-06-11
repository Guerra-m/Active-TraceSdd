## ADDED Requirements

### Requirement: Cliente HTTP centralizado con Bearer token
El sistema SHALL proveer un cliente Axios exportado desde `@/shared/services/api`. Cada request SHALL incluir automáticamente el header `Authorization: Bearer <access_token>` cuando haya una sesión activa. Componentes y hooks SHALL consumir únicamente este cliente; nunca instanciar Axios directamente.

#### Scenario: Request autenticado incluye header Bearer
- **WHEN** un hook llama a `api.get('/api/materias')` con sesión activa
- **THEN** el request HTTP contiene el header `Authorization: Bearer <token>` con el access token actual

#### Scenario: Request sin sesión no incluye header Bearer
- **WHEN** un hook llama a `api.post('/api/auth/login', body)` sin sesión activa
- **THEN** el request HTTP no contiene el header `Authorization`

### Requirement: Refresh transparente al recibir 401
El sistema SHALL interceptar respuestas 401 del servidor, ejecutar un refresh silencioso vía `POST /api/auth/refresh` (usando la cookie httpOnly), actualizar el access token en memoria y reintentar el request original con el nuevo token. Si el refresh falla (respuesta no-2xx), el sistema SHALL limpiar la sesión y redirigir a `/login`.

#### Scenario: Request con token expirado se reintenta con token renovado
- **WHEN** un request recibe 401 y el refresh token es válido
- **THEN** el cliente ejecuta refresh, obtiene nuevo access token y reintenta el request original obteniendo la respuesta correcta

#### Scenario: Múltiples requests 401 simultáneos no generan múltiples refreshes
- **WHEN** tres requests simultáneos reciben 401 al mismo tiempo
- **THEN** sólo se ejecuta una llamada a `/api/auth/refresh`; los tres requests se resuelven con el nuevo token

#### Scenario: Refresh fallido redirige a login
- **WHEN** un request recibe 401 y el refresh token está expirado o es inválido
- **THEN** el cliente limpia el access token en memoria y redirige el browser a `/login`

### Requirement: Propagación de errores 403
El sistema SHALL propagar errores 403 sin retry. El componente que realizó la llamada SHALL recibir el error para manejarlo (mostrar mensaje "Sin permiso" o redirigir).

#### Scenario: Error 403 se propaga al llamador
- **WHEN** un request recibe respuesta 403
- **THEN** la promesa rechaza con un error tipado `{ status: 403, message: "Forbidden" }` sin ningún retry

### Requirement: Proxy de desarrollo a la API
El sistema SHALL configurar en `vite.config.ts` un proxy de `server.proxy` que mapee `/api` a `http://localhost:8000` para que el frontend en dev no tenga problemas de CORS.

#### Scenario: Llamada a /api en dev llega al backend
- **WHEN** el frontend en dev hace `GET /api/health`
- **THEN** Vite proxy reenvía la request a `http://localhost:8000/api/health` y devuelve la respuesta al browser
