import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { EncuentrosAdminPage } from './EncuentrosAdminPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as encuentrosService from '../services/encuentrosAdminService'
import type { PagedResponse, EncuentroAdmin } from '../types'

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

const mockEncuentro: EncuentroAdmin = {
  id: 'enc-1',
  alumno_id: 'al-1',
  alumno_nombre: 'María López',
  tutor_id: 'tut-1',
  tutor_nombre: 'Prof. García',
  fecha: '2024-08-10',
  hora: '14:00',
  tipo: 'individual',
  estado: 'programado',
  tenant_id: 't1',
}

const mockList: PagedResponse<EncuentroAdmin> = {
  items: [mockEncuentro],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('EncuentrosAdminPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de encuentros con permiso encuentros:gestionar', async () => {
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => {
      expect(screen.getByText('María López')).toBeInTheDocument()
    })
    expect(screen.getByText('Prof. García')).toBeInTheDocument()
    expect(screen.getByText('Programado')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso encuentros:gestionar', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<EncuentrosAdminPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('abre modal de slots recurrentes al hacer clic', async () => {
    const user = userEvent.setup()
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => screen.getByText('María López'))
    await user.click(screen.getByRole('button', { name: /crear slots recurrentes/i }))

    expect(screen.getByRole('heading', { name: /crear slots recurrentes/i })).toBeInTheDocument()
  })

  it('valida formulario de slots sin día seleccionado', async () => {
    const user = userEvent.setup()
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => screen.getByText('María López'))
    await user.click(screen.getByRole('button', { name: /crear slots recurrentes/i }))

    // Submit without filling fields
    await user.click(screen.getByRole('button', { name: /^crear slots$/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
