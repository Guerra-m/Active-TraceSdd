## Context

El backend de autenticación (C-03) y RBAC (C-04) están operativos. No existe capa de presentación. Este change introduce toda la infraestructura frontend: el proyecto Vite/React, el cliente HTTP con manejo transparente de tokens y las pantallas de autenticación que consumen los endpoints ya existentes.

El frontend vive en `frontend/` dentro del monorepo. En desarrollo corre con Vite dev server (proxy a la API en `localhost:8000`). En producción se sirve como static build desde Nginx dentro de Docker.

## Goals / Non-Goals

**Goals:**
- Scaffold completo del proyecto frontend (Vite + React 18 + TypeScript + Tailwind + TanStack Query + React Hook Form + Zod).
- Cliente HTTP centralizado con refresh transparente de tokens (access token en memoria, refresh token en cookie httpOnly).
- Pantallas: login, 2FA TOTP, recuperación de contraseña.
- Guard `RequireAuth` y `RequirePermission` para proteger rutas.
- Layout principal (sidebar + topbar) con menú dinámico según permisos del JWT.

**Non-Goals:**
- Ninguna feature de dominio (importación, alumnos, comunicaciones, etc.) — eso es C-22/C-23/C-24.
- Internacionalización (i18n).
- SSR / Next.js.
- Tema oscuro.

## Decisions

### D-01: Access token en memoria, refresh en cookie httpOnly

Access token se guarda en una variable JS en memoria (no localStorage/sessionStorage). Refresh token se guarda en cookie httpOnly seteada por el backend.

**Alternativa descartada**: localStorage — vulnerable a XSS.

**Rationale**: Elimina el vector XSS para el access token. La cookie httpOnly es inaccesible desde JS. Al recargar la página se ejecuta un silent refresh automático vía `GET /api/auth/refresh` antes de renderizar rutas protegidas.

### D-02: Interceptor Axios con cola de reintentos durante refresh

Si múltiples requests simultáneos reciben 401, sólo uno dispara el refresh; los demás se encolan y se resuelven con el nuevo token cuando el refresh termina. Si el refresh falla, toda la cola rechaza y se redirige a `/login`.

**Alternativa descartada**: retry naïve sin cola — genera múltiples llamadas a `/api/auth/refresh` en paralelo, provocando invalidación prematura del refresh token por la rotación.

### D-03: Context + hook `useAuth()` como única fuente de verdad de identidad

El estado de sesión (usuario, permisos, token) vive en `AuthContext`. Componentes sólo consumen `useAuth()`. El contexto NO persiste en localStorage; se rehidrata desde el silent refresh inicial.

**Rationale**: Un solo punto de acceso facilita el testing (mock del context) y previene divergencias entre múltiples fuentes de estado.

### D-04: Tailwind con design tokens centralizados en `tailwind.config.ts`

Colores, tipografías y breakpoints de la marca definen en el config, no como clases arbitrarias. Sin CSS Modules ni estilos inline salvo valores dinámicos que no se pueden expresar como clases Tailwind.

### D-05: Vitest + Testing Library para tests unitarios y de integración

**Alternativa descartada**: Jest — más lento, requiere configuración adicional con Vite. Vitest reutiliza la config de Vite sin overhead.

E2E queda fuera de scope de este change (se agrega en un change dedicado de calidad).

## Risks / Trade-offs

- **[Riesgo] Silent refresh al cargar la app añade latencia** → Mitigation: mostrar spinner global mientras el refresh está en vuelo; si el refresh tarda >3s mostrar error y redirigir a login.
- **[Riesgo] Cookie httpOnly requiere que el backend setee `SameSite=Strict` y `Secure` en producción** → Mitigation: verificar config del backend en C-03; documentar en README. En dev funciona sin `Secure` (HTTP localhost).
- **[Trade-off] Access token en memoria se pierde al cerrar la pestaña** → Aceptado: el silent refresh lo recupera en ≤500ms al reabrir.
- **[Riesgo] El menú dinámico por permisos decodifica el JWT en el cliente** → Mitigation: nunca confiar en los permisos del lado cliente para tomar decisiones de seguridad; el backend valida en cada request. El menú es UX, no seguridad.
