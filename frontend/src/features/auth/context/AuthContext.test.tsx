import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import * as apiModule from '@/shared/services/api'

// Componente auxiliar para testear el hook
function TestConsumer() {
  const auth = useAuth()
  return (
    <div>
      <span data-testid="user">{auth.user?.email ?? 'null'}</span>
      <span data-testid="token">{auth.accessToken ?? 'null'}</span>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('3.4 - silent refresh exitoso rehidrata la sesión', async () => {
    const mockUser = {
      id: '1',
      email: 'user@test.com',
      nombre: 'Test User',
      rol: 'ALUMNO',
      tenant_id: 'tenant-1',
    }

    vi.spyOn(apiModule.api, 'post').mockResolvedValueOnce({
      data: {
        access_token: 'new-token-123',
        user: mockUser,
        permissions: ['alumnos:read'],
      },
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('user@test.com')
    })
    expect(screen.getByTestId('token')).toHaveTextContent('new-token-123')
  })

  it('3.5 - silent refresh fallido deja sesión como null sin lanzar error', async () => {
    vi.spyOn(apiModule.api, 'post').mockRejectedValueOnce(new Error('Unauthorized'))

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null')
    })
    expect(screen.getByTestId('token')).toHaveTextContent('null')
  })

  it('useAuth lanza error si se usa fuera del provider', () => {
    // Silenciar el error de React en test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestConsumer />)
    }).toThrow('useAuth debe usarse dentro de <AuthProvider>')

    consoleSpy.mockRestore()
  })
})
