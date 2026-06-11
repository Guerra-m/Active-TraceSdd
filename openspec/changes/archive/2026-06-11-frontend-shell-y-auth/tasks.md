## 1. Scaffold del proyecto frontend

- [x] 1.1 Crear `frontend/` con `npm create vite@latest -- --template react-ts`; configurar `tsconfig.json` con `strict: true` y path alias `@/ → src/`
- [x] 1.2 Instalar dependencias: `tailwindcss`, `@tanstack/react-query`, `axios`, `react-hook-form`, `zod`, `@hookform/resolvers`, `react-router-dom`
- [x] 1.3 Configurar Tailwind (`tailwind.config.ts` con tokens de colores/tipografía del proyecto, `postcss.config.ts`)
- [x] 1.4 Configurar proxy en `vite.config.ts`: `/api → http://localhost:8000`
- [x] 1.5 Crear estructura de directorios base: `src/features/`, `src/shared/`, `src/shared/services/`, `src/shared/components/`, `src/shared/hooks/`
- [x] 1.6 Instalar Vitest + Testing Library: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`; configurar `vitest.config.ts`

## 2. Cliente HTTP centralizado

- [x] 2.1 Implementar `src/shared/services/api.ts`: instancia Axios con `baseURL: '/api'`, interceptor de request que inyecta `Authorization: Bearer <token>` desde el store de sesión
- [x] 2.2 Implementar cola de reintentos en el interceptor de response: captura 401, ejecuta refresh silencioso, reencola los requests en vuelo y los resuelve con el nuevo token
- [x] 2.3 Implementar lógica de logout forzado cuando el refresh falla (limpia token + redirige a `/login`)
- [x] 2.4 Test: interceptor inyecta Bearer cuando hay token activo
- [x] 2.5 Test: múltiples 401 simultáneos disparan sólo un refresh; todos se resuelven con el nuevo token
- [x] 2.6 Test: refresh fallido redirige a `/login` y limpia el token

## 3. Contexto de autenticación (AuthContext)

- [x] 3.1 Implementar `src/features/auth/context/AuthContext.tsx`: estado `{ user, permissions, accessToken }`, setter interno y función `logout()`
- [x] 3.2 Implementar hook `useAuth()` que consume el contexto; lanzar error si se usa fuera del provider
- [x] 3.3 Implementar `AuthProvider`: al montar, ejecutar silent refresh (`POST /api/auth/refresh`); mostrar spinner global mientras está en vuelo; si falla dejar sesión como `null`
- [x] 3.4 Test: silent refresh exitoso rehidrata la sesión (mock de API)
- [x] 3.5 Test: silent refresh fallido deja sesión como null sin lanzar error

## 4. Guards de rutas

- [x] 4.1 Implementar `<RequireAuth>`: si sesión null → redirigir a `/login?redirect=<ruta actual>`; si hay sesión → renderizar children
- [x] 4.2 Implementar `<RequirePermission permission="modulo:accion" fallback={...}>`: verificar permiso desde `useAuth()`; sin permiso → renderizar fallback o mensaje por defecto
- [x] 4.3 Test: `<RequireAuth>` redirige a `/login` cuando no hay sesión
- [x] 4.4 Test: `<RequireAuth>` renderiza children cuando hay sesión válida
- [x] 4.5 Test: `<RequirePermission>` renderiza fallback cuando el usuario no tiene el permiso

## 5. Pantallas de autenticación

- [x] 5.1 Implementar `LoginPage` (`/login`): formulario email+password con validación Zod; llama a `POST /api/auth/login`; maneja respuesta con/sin `requires_2fa`
- [x] 5.2 Implementar `TwoFactorPage` (`/login/2fa`): formulario de código TOTP 6 dígitos; llama a `POST /api/auth/2fa/verify`; redirige a `/login` si accede sin `temp_token`
- [x] 5.3 Implementar `ForgotPasswordPage` (`/login/forgot`): formulario email; llama a `POST /api/auth/forgot`; muestra confirmación genérica
- [x] 5.4 Implementar `ResetPasswordPage` (`/login/reset`): formulario nueva contraseña + confirmación; lee `token` de query param; llama a `POST /api/auth/reset`
- [x] 5.5 Test: `LoginPage` render y validación inline con campos inválidos
- [x] 5.6 Test: `LoginPage` flujo exitoso sin 2FA → redirige a dashboard
- [x] 5.7 Test: `LoginPage` flujo con `requires_2fa: true` → redirige a `/login/2fa`
- [x] 5.8 Test: `TwoFactorPage` redirige a `/login` cuando no hay `temp_token`
- [x] 5.9 Test: `LoginPage` muestra error en credenciales inválidas (401)

## 6. Layout principal

- [x] 6.1 Implementar `AppLayout`: sidebar con navegación + topbar con nombre/rol del usuario; envuelve las rutas protegidas
- [x] 6.2 Implementar configuración del menú: array de `{ label, path, permission }` filtrado por `useAuth()` para mostrar solo ítems con permiso
- [x] 6.3 Implementar botón de logout en topbar que invoca `useAuth().logout()`
- [x] 6.4 Test: sidebar muestra ítems sólo para los permisos presentes en el token (mock de `useAuth`)
- [x] 6.5 Test: topbar muestra nombre del usuario autenticado

## 7. Routing principal

- [x] 7.1 Configurar `src/router.tsx` con `createBrowserRouter`: rutas públicas (`/login`, `/login/2fa`, `/login/forgot`, `/login/reset`) y rutas protegidas bajo `<RequireAuth>` con `<AppLayout>`
- [x] 7.2 Configurar `QueryClientProvider` + `AuthProvider` en `src/main.tsx`

## 8. Docker e integración

- [x] 8.1 Escribir `frontend/Dockerfile` multi-stage: etapa `build` (Node 20 Alpine, `npm ci && npm run build`) y etapa `serve` (Nginx Alpine, config SPA fallback + proxy `/api`)
- [x] 8.2 Agregar servicio `frontend` en `docker-compose.yml` raíz (puerto 3000:80, depends_on: api)
- [x] 8.3 Verificar que `docker compose up` levanta api + frontend sin errores y `GET http://localhost:3000` devuelve la SPA
