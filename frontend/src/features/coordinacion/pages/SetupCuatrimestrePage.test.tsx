import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { SetupCuatrimestrePage } from './SetupCuatrimestrePage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as equiposService from '../services/equiposService'
import type { ClonarEquipoResponse } from '../services/equiposService'

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

const mockClonarResponse: ClonarEquipoResponse = {
  creadas: 3,
  conflictos: 0,
  asignaciones: [],
  omitidos: [],
}

describe('SetupCuatrimestrePage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra fallback sin permiso equipos:asignar', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<SetupCuatrimestrePage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('muestra paso 1 con permiso equipos:asignar', () => {
    mockAuth(['equipos:asignar'])

    renderWithProviders(<SetupCuatrimestrePage />)

    expect(screen.getByText(/paso 1/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ID Materia/i)).toBeInTheDocument()
  })

  it('valida campos vacíos en paso 1', async () => {
    const user = userEvent.setup()
    mockAuth(['equipos:asignar'])

    renderWithProviders(<SetupCuatrimestrePage />)

    await user.click(screen.getByRole('button', { name: /clonar y continuar/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })

  it('avanza a paso 2 después de clonar exitosamente', async () => {
    const user = userEvent.setup()
    mockAuth(['equipos:asignar'])
    vi.spyOn(equiposService, 'clonarEquipo').mockResolvedValue(mockClonarResponse)

    renderWithProviders(<SetupCuatrimestrePage />)

    await user.type(screen.getByLabelText(/ID Materia/i), 'mat-1')
    await user.type(screen.getByLabelText(/ID Carrera/i), 'carr-1')
    await user.type(screen.getByLabelText(/Cohorte origen/i), 'coh-1')
    await user.type(screen.getByLabelText(/Cohorte destino/i), 'coh-2')
    await user.type(screen.getByLabelText(/Vigencia desde/i), '2024-08-01')
    await user.click(screen.getByRole('button', { name: /clonar y continuar/i }))

    await waitFor(() => {
      expect(screen.getByText(/paso 2/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/equipo clonado exitosamente/i)).toBeInTheDocument()
  })
})
