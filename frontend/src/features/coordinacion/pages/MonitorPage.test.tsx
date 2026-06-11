import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { MonitorPage } from './MonitorPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as monitorService from '../services/monitorService'
import type { MonitorMetrics } from '../types'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(createElement(QueryClientProvider, { client: queryClient }, ui))
}

function mockAuth(permissions: string[]) {
  vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
    user: { id: '1', email: 'coord@test.com', nombre: 'Coord', rol: 'COORDINADOR', tenant_id: 't1' },
    permissions,
    accessToken: 'token',
    setAuth: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  })
}

const mockMetrics: MonitorMetrics = {
  alumnos_atrasados: 7,
  entregas_pendientes: 15,
  comunicaciones_enviadas: 42,
  tasa_contacto: 0.78,
  resumen_por_materia: [
    { materia_id: 'm1', materia_nombre: 'Física I', atrasados: 4, al_dia: 18 },
  ],
}

describe('MonitorPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra métricas del monitor con permiso atrasados:ver', async () => {
    mockAuth(['atrasados:ver'])
    vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)

    renderWithProviders(<MonitorPage />)

    await waitFor(() => {
      expect(screen.getByText('7')).toBeInTheDocument()
    })
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('78%')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso atrasados:ver', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<MonitorPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('muestra error de validación cuando hasta es anterior a desde', async () => {
    const user = userEvent.setup()
    mockAuth(['atrasados:ver'])
    vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)

    renderWithProviders(<MonitorPage />)

    await waitFor(() => screen.getByLabelText(/desde/i))

    await user.type(screen.getByLabelText(/desde/i), '2024-07-01')
    await user.type(screen.getByLabelText(/hasta/i), '2024-06-01')
    await user.click(screen.getByRole('button', { name: /aplicar filtro/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('muestra resumen por materia', async () => {
    mockAuth(['atrasados:ver'])
    vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)

    renderWithProviders(<MonitorPage />)

    await waitFor(() => {
      expect(screen.getByText('Física I')).toBeInTheDocument()
    })
  })
})
