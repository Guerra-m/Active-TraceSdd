import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { EquiposPage } from './EquiposPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as equiposService from '../services/equiposService'
import type { PagedResponse, Equipo } from '../types'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    createElement(QueryClientProvider, { client: queryClient }, ui),
  )
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

const mockEquipoList: PagedResponse<Equipo> = {
  items: [
    {
      id: 'eq-1',
      nombre: 'Equipo Alpha',
      periodo: '2024-1',
      fecha_inicio: '2024-03-01',
      fecha_fin: '2024-07-31',
      tutores_count: 5,
      tenant_id: 't1',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('EquiposPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de equipos con permiso equipos:asignar', async () => {
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockEquipoList)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => {
      expect(screen.getByText('Equipo Alpha')).toBeInTheDocument()
    })
    expect(screen.getByText('2024-1')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso equipos:asignar', () => {
    mockAuth(['alumnos:read'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockEquipoList)

    renderWithProviders(<EquiposPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
    expect(screen.queryByText('Equipo Alpha')).not.toBeInTheDocument()
  })

  it('muestra error cuando la carga falla', async () => {
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockRejectedValue(new Error('Network error'))

    renderWithProviders(<EquiposPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('abre modal de clonar al hacer clic en Clonar', async () => {
    const user = userEvent.setup()
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockEquipoList)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => screen.getByText('Equipo Alpha'))

    await user.click(screen.getByRole('button', { name: /clonar/i }))

    expect(screen.getByText(/clonar equipo: Equipo Alpha/i)).toBeInTheDocument()
  })

  it('valida período destino vacío en modal de clonar', async () => {
    const user = userEvent.setup()
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockEquipoList)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => screen.getByText('Equipo Alpha'))
    // Open the clone modal
    await user.click(screen.getByRole('button', { name: /^clonar$/i }))

    // Modal should be visible
    const modalHeading = screen.getByRole('heading', { name: /clonar equipo/i })
    expect(modalHeading).toBeInTheDocument()

    // Find the submit button inside the modal (type=submit)
    const submitButtons = screen.getAllByRole('button', { name: /^clonar$/i })
    const submitBtn = submitButtons.find((b) => b.getAttribute('type') === 'submit')
    expect(submitBtn).toBeDefined()
    await user.click(submitBtn!)

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
