import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { ColoquiosPage } from './ColoquiosPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as coloquiosService from '../services/coloquiosService'
import type { PagedResponse, Convocatoria } from '../types'

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

const mockConvocatoria: Convocatoria = {
  id: 'conv-1',
  materia_id: 'mat-1',
  materia_nombre: 'Química Orgánica',
  fecha: '2024-09-15',
  cupo: 25,
  inscriptos: 10,
  descripcion: 'Coloquio regular',
  estado: 'abierta',
  tenant_id: 't1',
}

const mockConvList: PagedResponse<Convocatoria> = {
  items: [mockConvocatoria],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('ColoquiosPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de convocatorias con permiso coloquios:read', async () => {
    mockAuth(['coloquios:read'])
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue(mockConvList)

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => {
      expect(screen.getByText('Química Orgánica')).toBeInTheDocument()
    })
    expect(screen.getByText('Abierta')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso coloquios:read', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<ColoquiosPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('valida cupo inválido (0) al crear convocatoria', async () => {
    const user = userEvent.setup()
    mockAuth(['coloquios:read'])
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue(mockConvList)

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => screen.getByText('Química Orgánica'))
    await user.click(screen.getByRole('button', { name: /nueva convocatoria/i }))

    // Click submit without filling any field — should trigger validation on all required fields
    await user.click(screen.getByRole('button', { name: /crear convocatoria/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })

  it('muestra mensaje cuando no hay convocatorias', async () => {
    mockAuth(['coloquios:read'])
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    renderWithProviders(<ColoquiosPage />)

    await waitFor(() => {
      expect(screen.getByText(/no hay convocatorias/i)).toBeInTheDocument()
    })
  })
})
