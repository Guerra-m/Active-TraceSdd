import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { EquiposPage } from './EquiposPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as equiposService from '../services/equiposService'
import type { AsignacionItem } from '../types'

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

const mockAsignaciones: AsignacionItem[] = [
  {
    id: 'asi-1',
    tenant_id: 't1',
    usuario_id: 'user-abc',
    rol: 'PROFESOR',
    materia_id: 'mat-1',
    carrera_id: 'car-1',
    cohorte_id: 'coh-1',
    comisiones: ['A'],
    responsable_id: null,
    desde: '2024-03-01',
    hasta: '2024-07-31',
    estado_vigencia: 'vigente',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('EquiposPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de equipos con permiso equipos:asignar', async () => {
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockAsignaciones)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => {
      expect(screen.getByText('user-abc')).toBeInTheDocument()
    })
    expect(screen.getByText('PROFESOR')).toBeInTheDocument()
    expect(screen.getByText('vigente')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso equipos:asignar', () => {
    mockAuth(['alumnos:read'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockAsignaciones)

    renderWithProviders(<EquiposPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
    expect(screen.queryByText('user-abc')).not.toBeInTheDocument()
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
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockAsignaciones)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => screen.getByText('user-abc'))

    await user.click(screen.getByRole('button', { name: /clonar/i }))

    expect(screen.getByText(/clonar equipo: PROFESOR/i)).toBeInTheDocument()
  })

  it('valida cohorte destino vacío en modal de clonar', async () => {
    const user = userEvent.setup()
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockAsignaciones)

    renderWithProviders(<EquiposPage />)

    await waitFor(() => screen.getByText('user-abc'))
    await user.click(screen.getByRole('button', { name: /^clonar$/i }))

    const modalHeading = screen.getByRole('heading', { name: /clonar equipo/i })
    expect(modalHeading).toBeInTheDocument()

    const submitButtons = screen.getAllByRole('button', { name: /^clonar$/i })
    const submitBtn = submitButtons.find((b) => b.getAttribute('type') === 'submit')
    expect(submitBtn).toBeDefined()
    await user.click(submitBtn!)

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
