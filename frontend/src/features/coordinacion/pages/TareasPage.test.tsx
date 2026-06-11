import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { TareasPage } from './TareasPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as tareasService from '../services/tareasService'
import type { Tarea } from '../types'

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

const mockTarea: Tarea = {
  id: 'tar-1',
  tenant_id: 't1',
  materia_id: null,
  asignado_a: 'user-1',
  asignado_por: 'admin-1',
  estado: 'Pendiente',
  descripcion: 'Revisión de notas finales',
  contexto_id: null,
  created_at: '2024-01-01T00:00:00Z',
}

const mockTareas: Tarea[] = [mockTarea]

const emptyTareas: Tarea[] = []

describe('TareasPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de tareas con permiso tareas:gestionar', async () => {
    mockAuth(['tareas:gestionar'])
    vi.spyOn(tareasService, 'fetchTareas').mockResolvedValue(mockTareas)

    renderWithProviders(<TareasPage />)

    await waitFor(() => {
      expect(screen.getByText('Revisión de notas finales')).toBeInTheDocument()
    })
    expect(screen.getByText(/user-1/i, { exact: false })).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay tareas asignadas', async () => {
    mockAuth(['tareas:gestionar'])
    vi.spyOn(tareasService, 'fetchTareas').mockResolvedValue(emptyTareas)

    renderWithProviders(<TareasPage />)

    await waitFor(() => {
      expect(screen.getByText(/no hay tareas asignadas/i)).toBeInTheDocument()
    })
  })

  it('muestra fallback sin permiso tareas:gestionar', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<TareasPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('valida campos requeridos al crear tarea', async () => {
    const user = userEvent.setup()
    mockAuth(['tareas:gestionar'])
    vi.spyOn(tareasService, 'fetchTareas').mockResolvedValue(emptyTareas)

    renderWithProviders(<TareasPage />)

    await waitFor(() => screen.getByRole('button', { name: /nueva tarea/i }))
    await user.click(screen.getByRole('button', { name: /nueva tarea/i }))
    await user.click(screen.getByRole('button', { name: /crear tarea/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
