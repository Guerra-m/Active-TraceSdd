import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/context/AuthContext'
import { Spinner } from '@/shared/components/Spinner'
import { RequireAuth } from '@/shared/components/RequireAuth'
import { AppLayout } from '@/features/layout/AppLayout'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
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
import { MateriasPage } from '@/features/admin/pages/MateriasPage'
import { AlumnosPage } from '@/features/admin/pages/AlumnosPage'
import { UsuariosAdminPage } from '@/features/admin/pages/UsuariosAdminPage'
import { AuditoriaPage } from '@/features/admin/pages/AuditoriaPage'
import { ComisionesPage } from '@/features/coordinacion/pages/ComisionesPage'

// Fallback para ADMIN/roles sin asignación propia (asignación del admin seeded)
const FALLBACK_ASIGNACION_ID = '8c17bf88-6eac-45c5-aff8-1bf59a17d9d0'
const FALLBACK_MATERIA_ID    = 'e4ebc2e4-2c3d-408f-8994-f465bb8adc02'

type WithAsignacionProps = { asignacionId: string; materiaId: string }

function ProfesorRoute({ Page }: { Page: React.ComponentType<WithAsignacionProps> }) {
  const { asignacion, isLoadingAsignacion } = useAuth()

  if (isLoadingAsignacion && !asignacion) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <Page
      asignacionId={asignacion?.asignacionId ?? FALLBACK_ASIGNACION_ID}
      materiaId={asignacion?.materiaId ?? FALLBACK_MATERIA_ID}
    />
  )
}

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
      { path: 'dashboard', element: <DashboardPage /> },
      // Páginas implementadas
      { path: 'alumnos', element: <AlumnosPage /> },
      { path: 'materias', element: <MateriasPage /> },
      { path: 'comisiones', element: <ComisionesPage /> },
      { path: 'comunicacion', element: <ProfesorRoute Page={ComunicacionesPage} /> },
      // Alias de rutas cortas → páginas ya implementadas
      { path: 'encuentros', element: <EncuentrosAdminPage /> },
      { path: 'liquidaciones', element: <LiquidacionesPage /> },
      { path: 'auditoria', element: <AuditoriaPage /> },
      { path: 'usuarios', element: <UsuariosAdminPage /> },
      // Módulo académico docente (C-22)
      { path: 'profesor/atrasados',      element: <ProfesorRoute Page={AtrasadosPage} /> },
      { path: 'profesor/importar',       element: <ProfesorRoute Page={ImportacionPage} /> },
      { path: 'profesor/umbral',         element: <ProfesorRoute Page={UmbralPage} /> },
      { path: 'profesor/entregas',       element: <ProfesorRoute Page={EntregasPage} /> },
      { path: 'profesor/comunicaciones', element: <ProfesorRoute Page={ComunicacionesPage} /> },
      { path: 'profesor/monitor',        element: <ProfesorRoute Page={MonitorPage} /> },
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
