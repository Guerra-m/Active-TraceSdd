## ADDED Requirements

### Requirement: Pantalla de login con validación
El sistema SHALL renderizar en `/login` un formulario con campos `email` y `password` validados con Zod (email válido, password no vacío). Al submit SHALL llamar a `POST /api/auth/login`. Si la respuesta incluye `requires_2fa: true`, SHALL redirigir a `/login/2fa`. Si la respuesta es 200 con tokens, SHALL almacenar el access token en memoria, marcar la sesión como activa y redirigir a `/dashboard`.

#### Scenario: Login exitoso sin 2FA redirige al dashboard
- **WHEN** el usuario ingresa credenciales válidas y el backend responde con tokens (sin `requires_2fa`)
- **THEN** el access token se guarda en memoria y el browser navega a `/dashboard`

#### Scenario: Login con 2FA requerido redirige a pantalla TOTP
- **WHEN** el backend responde con `{ requires_2fa: true, temp_token: "..." }`
- **THEN** el browser navega a `/login/2fa` con el `temp_token` disponible para el siguiente paso

#### Scenario: Credenciales inválidas muestran mensaje de error
- **WHEN** el backend responde con 401 al intentar login
- **THEN** el formulario muestra "Credenciales incorrectas" sin revelar si el email existe

#### Scenario: Formulario bloquea submit con campos inválidos
- **WHEN** el usuario hace submit con email sin formato válido o password vacío
- **THEN** se muestran mensajes de validación inline y no se realiza ninguna llamada a la API

### Requirement: Pantalla 2FA TOTP
El sistema SHALL renderizar en `/login/2fa` un formulario con campo de código TOTP de 6 dígitos. Al submit SHALL llamar a `POST /api/auth/2fa/verify` con el `temp_token` y el código. Si la respuesta es 200, SHALL completar el flujo de sesión igual que login exitoso. Si falla, SHALL mostrar error.

#### Scenario: Código TOTP correcto completa la sesión
- **WHEN** el usuario ingresa el código TOTP correcto
- **THEN** se obtienen los tokens definitivos, el access token se guarda en memoria y navega a `/dashboard`

#### Scenario: Código TOTP incorrecto muestra error
- **WHEN** el backend responde con 401 al verificar TOTP
- **THEN** el formulario muestra "Código incorrecto" y permite reintentar

#### Scenario: Acceder a /login/2fa sin temp_token redirige a /login
- **WHEN** el usuario navega directamente a `/login/2fa` sin temp_token previo
- **THEN** el browser redirige a `/login`

### Requirement: Pantalla de recuperación de contraseña
El sistema SHALL renderizar en `/login/forgot` un formulario con campo `email`. Al submit SHALL llamar a `POST /api/auth/forgot`. En `/login/reset` SHALL mostrar el formulario de nueva contraseña (campos `password` y `confirmPassword`, token por query param) llamando a `POST /api/auth/reset`.

#### Scenario: Solicitud de recuperación enviada exitosamente
- **WHEN** el usuario ingresa su email y el backend responde con 200
- **THEN** se muestra el mensaje "Revisá tu correo" sin revelar si el email existe

#### Scenario: Reset de contraseña con token válido
- **WHEN** el usuario accede a `/login/reset?token=abc` y completa el formulario
- **THEN** se llama a `POST /api/auth/reset` con el token y las contraseñas; si es 200 redirige a `/login`

### Requirement: Guard RequireAuth
El sistema SHALL proveer el componente `<RequireAuth>` que envuelve rutas protegidas. Si no hay sesión activa (y el silent refresh inicial falló), SHALL redirigir a `/login` preservando la ruta original en `?redirect=`. Si hay sesión activa, SHALL renderizar el children.

#### Scenario: Usuario sin sesión es redirigido a login
- **WHEN** un usuario sin sesión navega a `/dashboard`
- **THEN** el browser redirige a `/login?redirect=/dashboard`

#### Scenario: Usuario con sesión válida ve el contenido
- **WHEN** un usuario con sesión válida navega a una ruta protegida
- **THEN** el componente renderiza sus children sin redirección

#### Scenario: Después de login con redirect, vuelve a la ruta original
- **WHEN** el usuario completa el login habiendo llegado desde `/login?redirect=/alumnos`
- **THEN** el browser navega a `/alumnos`

### Requirement: Guard RequirePermission
El sistema SHALL proveer el componente `<RequirePermission permission="modulo:accion">` que muestra sus children sólo si el usuario tiene el permiso especificado, o renderiza un fallback de "Sin acceso" (configurable via prop `fallback`).

#### Scenario: Usuario con permiso ve el contenido
- **WHEN** un usuario con permiso `equipos:asignar` accede a un componente envuelto en `<RequirePermission permission="equipos:asignar">`
- **THEN** el componente renderiza sus children

#### Scenario: Usuario sin permiso ve el fallback
- **WHEN** un usuario sin el permiso accede al componente
- **THEN** se renderiza el `fallback` prop o el mensaje por defecto "No tenés permiso para ver esta sección"

### Requirement: Silent refresh al cargar la app
El sistema SHALL ejecutar un silent refresh (`POST /api/auth/refresh`) antes de resolver el primer render de rutas protegidas. Si el refresh responde 200, SHALL guardar el access token en memoria y continuar. Si falla, SHALL dejar la sesión como `null` (no hay sesión). Mientras el refresh está en vuelo, SHALL mostrar un spinner global.

#### Scenario: Token válido en cookie restaura la sesión al recargar
- **WHEN** el usuario recarga la página con un refresh token válido en cookie
- **THEN** el silent refresh obtiene un nuevo access token, la sesión queda activa y el usuario no ve el formulario de login

#### Scenario: Sin cookie válida la sesión queda como null
- **WHEN** el usuario recarga la página sin cookie de refresh token
- **THEN** el silent refresh falla silenciosamente y la sesión queda como null; navegar a ruta protegida redirige a `/login`

### Requirement: Logout con revocación de sesión
El sistema SHALL proveer la acción `logout()` accesible desde `useAuth()`. Al invocarse SHALL llamar a `POST /api/auth/logout`, limpiar el access token en memoria y redirigir a `/login`.

#### Scenario: Logout limpia sesión y redirige
- **WHEN** el usuario hace clic en "Cerrar sesión"
- **THEN** se llama a `/api/auth/logout`, el access token se elimina de memoria y el browser navega a `/login`
