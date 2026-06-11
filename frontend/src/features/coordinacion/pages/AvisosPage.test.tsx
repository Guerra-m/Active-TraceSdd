import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { AvisosPage } from './AvisosPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import * as avisosService from '../services/avisosService'
import type { PagedResponse, Aviso } from '../types'

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

const mockAviso: Aviso = {
  id: 'av-1',
  titulo: 'Aviso de prueba',
  cuerpo: 'Cuerpo del aviso',
  scope: 'Global',
  estado: 'publicado',
  fecha_publicacion: '2024-06-01',
  fecha_expiracion: null,
  requiere_ack: false,
  leido_por_mi: false,
  tenant_id: 't1',
}

const mockAvisoList: PagedResponse<Aviso> = {
  items: [mockAviso],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('AvisosPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra listado de avisos con permiso avisos:publicar', async () => {
    mockAuth(['avisos:publicar'])
    vi.spyOn(avisosService, 'fetchAvisos').mockResolvedValue(mockAvisoList)

    renderWithProviders(<AvisosPage />)

    await waitFor(() => {
      expect(screen.getByText('Aviso de prueba')).toBeInTheDocument()
    })
    expect(screen.getByText('Global')).toBeInTheDocument()
  })

  it('muestra fallback sin permiso avisos:publicar', () => {
    mockAuth(['alumnos:read'])

    renderWithProviders(<AvisosPage />)

    expect(screen.getByText(/no tenés permiso/i)).toBeInTheDocument()
  })

  it('abre modal de nuevo aviso al hacer clic', async () => {
    const user = userEvent.setup()
    mockAuth(['avisos:publicar'])
    vi.spyOn(avisosService, 'fetchAvisos').mockResolvedValue(mockAvisoList)

    renderWithProviders(<AvisosPage />)

    await waitFor(() => screen.getByText('Aviso de prueba'))
    await user.click(screen.getByRole('button', { name: /nuevo aviso/i }))

    expect(screen.getByRole('heading', { name: /nuevo aviso/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/título/i)).toBeInTheDocument()
  })

  it('valida título vacío al crear aviso', async () => {
    const user = userEvent.setup()
    mockAuth(['avisos:publicar'])
    vi.spyOn(avisosService, 'fetchAvisos').mockResolvedValue(mockAvisoList)

    renderWithProviders(<AvisosPage />)

    await waitFor(() => screen.getByText('Aviso de prueba'))
    await user.click(screen.getByRole('button', { name: /nuevo aviso/i }))
    await user.click(screen.getByRole('button', { name: /^guardar$/i }))

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })
})
