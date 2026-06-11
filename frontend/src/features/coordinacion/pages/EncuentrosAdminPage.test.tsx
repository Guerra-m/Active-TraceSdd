import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { EncuentrosAdminPage } from './EncuentrosAdminPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as encuentrosService from '../services/encuentrosAdminService'
import type { EncuentroAdmin } from '../types'

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
  tenant_id: 't1',
  slot_id: null,
  materia_id: 'mat-1',
  fecha: '2024-08-10',
  hora: '14:00',
  titulo: 'Encuentro de seguimiento',
  estado: 'Programado',
  meet_url: null,
  video_url: null,
  comentario: null,
}

const mockList: EncuentroAdmin[] = [mockEncuentro]

describe('EncuentrosAdminPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de encuentros con permiso encuentros:gestionar', async () => {
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => {
      expect(screen.getByText('Encuentro de seguimiento')).toBeInTheDocument()
    })
    expect(screen.getByText('2024-08-10')).toBeInTheDocument()
    expect(screen.getByText('Programado')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso encuentros:gestionar', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<EncuentrosAdminPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('abre modal de slots al hacer clic', async () => {
    const user = userEvent.setup()
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => screen.getByText('Encuentro de seguimiento'))
    await user.click(screen.getByRole('button', { name: /crear slot/i }))

    expect(screen.getByRole('heading', { name: /crear slot/i })).toBeInTheDocument()
  })

  it('valida formulario de slots sin campos requeridos', async () => {
    const user = userEvent.setup()
    mockAuth(['encuentros:gestionar'])
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    renderWithProviders(<EncuentrosAdminPage />)

    await waitFor(() => screen.getByText('Encuentro de seguimiento'))
    await user.click(screen.getByRole('button', { name: /crear slot/i }))

    const submitButtons = screen.getAllByRole('button', { name: /^crear slot$/i })
    await user.click(submitButtons[submitButtons.length - 1])

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
