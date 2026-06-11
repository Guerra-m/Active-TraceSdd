import { createBrowserRouter, Navigate } from 'react-router-dom'
import { RequireAuth } from '@/shared/components/RequireAuth'
import { AppLayout } from '@/features/layout/AppLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { TwoFactorPage } from '@/features/auth/pages/TwoFactorPage'
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage'
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage'
import { AtrasadosPage } from '@/features/academico/pages/AtrasadosPage'
import { ImportacionPage } from '@/features/academico/pages/ImportacionPage'
import { UmbralPage } from '@/features/academico/pages/UmbralPage'
import { EntregasPage } from '@/features/academico/pages/EntregasPage'
import { ComunicacionesPage } from '@/features/academico/pages/ComunicacionesPage'
import { MonitorPage } from '@/features/academico/pages/MonitorPage'
import { EquiposPage } from '@/features/coordinacion/pages/EquiposPage'
import { AvisosPage } from '@/features/coordinacion/pages/AvisosPage'
import { TareasPage } from '@/features/coordinacion/pages/TareasPage'
import { MonitorPage as CoordinacionMonitorPage } from '@/features/coordinacion/pages/MonitorPage'
import { EncuentrosAdminPage } from '@/features/coordinacion/pages/EncuentrosAdminPage'
import { ColoquiosPage } from '@/features/coordinacion/pages/ColoquiosPage'
import { SetupCuatrimestrePage } from '@/features/coordinacion/pages/SetupCuatrimestrePage'
// Finanzas (C-24)
import { LiquidacionesPage } from '@/features/finanzas/pages/LiquidacionesPage'
import { GrillaSalarialPage } from '@/features/finanzas/pages/GrillaSalarialPage'
import { FacturasPage } from '@/features/finanzas/pages/FacturasPage'
// Admin (C-24)
import { EstructuraAcademicaPage } from '@/features/admin/pages/EstructuraAcademicaPage'
import { UsuariosAdminPage } from '@/features/admin/pages/UsuariosAdminPage'
import { AuditoriaPage } from '@/features/admin/pages/AuditoriaPage'

// Comision ID placeholder — en producción viene del contexto del usuario (sesión)
const DEFAULT_COMISION_ID = ''

export const router = createBrowserRouter([
  // Rutas públicas
  { path: '/login', element: <LoginPage /> },
  { path: '/login/2fa', element: <TwoFactorPage /> },
  { path: '/login/forgot', element: <ForgotPasswordPage /> },
  { path: '/login/reset', element: <ResetPasswordPage /> },

  // Rutas protegidas
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      {
        path: 'dashboard',
        element: <div className="p-6"><h1 className="text-2xl font-bold">Dashboard</h1></div>,
      },
      // Módulo académico docente (C-22)
      {
        path: 'profesor/atrasados',
        element: <AtrasadosPage comisionId={DEFAULT_COMISION_ID} />,
      },
      {
        path: 'profesor/importar',
        element: <ImportacionPage comisionId={DEFAULT_COMISION_ID} />,
      },
      {
        path: 'profesor/umbral',
        element: <UmbralPage comisionId={DEFAULT_COMISION_ID} />,
      },
      {
        path: 'profesor/entregas',
        element: <EntregasPage comisionId={DEFAULT_COMISION_ID} />,
      },
      {
        path: 'profesor/comunicaciones',
        element: <ComunicacionesPage comisionId={DEFAULT_COMISION_ID} />,
      },
      {
        path: 'profesor/monitor',
        element: <MonitorPage comisionId={DEFAULT_COMISION_ID} />,
      },
      // Módulo coordinación (C-23)
      { path: 'equipos', element: <EquiposPage /> },
      { path: 'avisos', element: <AvisosPage /> },
      { path: 'tareas', element: <TareasPage /> },
      { path: 'monitor', element: <CoordinacionMonitorPage /> },
      { path: 'encuentros/admin', element: <EncuentrosAdminPage /> },
      { path: 'coloquios', element: <ColoquiosPage /> },
      { path: 'setup-cuatrimestre', element: <SetupCuatrimestrePage /> },
      // Módulo finanzas (C-24)
      { path: 'finanzas/liquidaciones', element: <LiquidacionesPage /> },
      { path: 'finanzas/grilla-salarial', element: <GrillaSalarialPage /> },
      { path: 'finanzas/facturas', element: <FacturasPage /> },
      // Módulo admin (C-24)
      { path: 'admin/estructura', element: <EstructuraAcademicaPage /> },
      { path: 'admin/usuarios', element: <UsuariosAdminPage /> },
      { path: 'admin/auditoria', element: <AuditoriaPage /> },
    ],
  },

  // Fallback
  { path: '*', element: <Navigate to="/" replace /> },
])
