## Why

El backend (C-01–C-20) está completo y expuesto vía API REST, pero no existe ninguna interfaz de usuario. C-21 sienta la base de toda la SPA: scaffolding, shell, routing con guards y el flujo de autenticación end-to-end consumiendo los endpoints de C-03.

## What Changes

- Nuevo proyecto frontend React 18 + TypeScript + Vite en `frontend/` con estructura feature-based.
- Cliente HTTP centralizado (Axios) con interceptor de auth y **refresh transparente** de tokens.
- Pantallas de autenticación: login, 2FA TOTP, recuperación de contraseña.
- Guard de rutas: redirige a `/login` si no hay sesión válida; bloquea con 403 si falta permiso.
- Layout principal (sidebar/topbar) con menú adaptado dinámicamente a los permisos del token.
- Logout con revocación de sesión vía `POST /api/auth/logout`.
- Tests: render de pantallas, flujo de auth (mock de API), guard redirige sin sesión, refresh transparente en 401.

## Capabilities

### New Capabilities
- `frontend-shell`: Scaffold Vite + React 18 + TS, estructura feature-based, Tailwind, TanStack Query, React Hook Form + Zod; layout principal con sidebar/topbar y menú dinámico por permisos.
- `frontend-http-client`: Cliente Axios centralizado en `@/shared/services/api`; interceptor que inyecta Bearer token, captura 401 y ejecuta refresh silencioso; propaga 403 sin retry.
- `frontend-auth-screens`: Pantallas login, 2FA TOTP y recuperación de contraseña; guard de rutas `RequireAuth` y `RequirePermission`; gestión del token en memoria + refresh token en cookie httpOnly.

### Modified Capabilities
- `user-auth`: Se agrega el flujo de presentación (login UI, 2FA UI, refresh transparente) al spec ya existente del backend de autenticación.

## Impact

- Nuevo directorio `frontend/` en la raíz del repo.
- `docker-compose.yml`: nuevo servicio `frontend` (Node/Vite dev, Nginx prod).
- Dependencias npm: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `axios`, `react-hook-form`, `zod`, `tailwindcss`, `typescript`, `vite`, `vitest`, `@testing-library/react`.
- No rompe ningún contrato de API existente.
