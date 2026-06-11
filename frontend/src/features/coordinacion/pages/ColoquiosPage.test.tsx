import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { ColoquiosPage } from './ColoquiosPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as coloquiosService from '../services/coloquiosService'
import type { EvaluacionItem, MetricasColoquio } from '../types'

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

const mockEvaluacion: EvaluacionItem = {
  id: 'ev-1',
  tenant_id: 't1',
  materia_id: 'mat-1',
  cohorte_id: 'coh-1',
  tipo: 'Coloquio',
  instancia: 'Coloquio Regular 2024',
  dias_disponibles: 3,
  cupos_por_dia: 10,
}

const mockMetricas: MetricasColoquio = {
  total_convocados: 30,
  instancias_activas: 1,
  reservas_activas: 5,
  notas_registradas: 20,
}

function setupDefaultMocks() {
  vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue([mockEvaluacion])
  vi.spyOn(coloquiosService, 'fetchMetricas').mockResolvedValue(mockMetricas)
}

describe('ColoquiosPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de convocatorias con permiso coloquios:read', async () => {
    mockAuth(['coloquios:read'])
    setupDefaultMocks()

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => {
      expect(screen.getByText('Coloquio Regular 2024')).toBeInTheDocument()
    })
    expect(screen.getByText('Coloquio')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso coloquios:read', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<ColoquiosPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('valida campos requeridos al crear convocatoria', async () => {
    const user = userEvent.setup()
    mockAuth(['coloquios:read'])
    setupDefaultMocks()

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => screen.getByText('Coloquio Regular 2024'))
    await user.click(screen.getByRole('button', { name: /nueva convocatoria/i }))

    await user.click(screen.getByRole('button', { name: /crear convocatoria/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })

  it('muestra mensaje cuando no hay convocatorias', async () => {
    mockAuth(['coloquios:read'])
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue([])
    vi.spyOn(coloquiosService, 'fetchMetricas').mockResolvedValue(mockMetricas)

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => {
      expect(screen.getByText(/no hay convocatorias/i)).toBeInTheDocument()
    })
  })
})
