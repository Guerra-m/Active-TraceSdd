import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import * as apiModule from '@/shared/services/api'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import type { AuthUser } from '@/features/auth/context/AuthContext'

function renderLoginPage(initialPath = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/login/2fa" element={<div>Página 2FA</div>} />
        <Route path="/dashboard" element={<div>Dashboard</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  const mockSetAuth = vi.fn()

  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      permissions: [],
      accessToken: null,
      setAuth: mockSetAuth,
      logout: vi.fn().mockResolvedValue(undefined),
    })
  })

  it('5.5 - render y validación inline con campos inválidos', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    const submitBtn = screen.getByRole('button', { name: /ingresar/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    })
  })

  it('5.6 - flujo exitoso sin 2FA redirige a dashboard', async () => {
    const user = userEvent.setup()
    const mockUser: AuthUser = {
      id: '1',
      email: 'user@test.com',
      nombre: 'Test',
      rol: 'ALUMNO',
      tenant_id: 't1',
    }

    vi.spyOn(apiModule.api, 'post').mockResolvedValueOnce({
      data: {
        requires_2fa: false,
        access_token: 'tok-123',
        user: mockUser,
        permissions: ['alumnos:read'],
      },
    })

    renderLoginPage()

    await user.type(screen.getByLabelText(/email/i), 'user@test.com')
    await user.type(screen.getByLabelText(/contraseña/i), 'password123')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
    expect(mockSetAuth).toHaveBeenCalledWith({
      user: mockUser,
      permissions: ['alumnos:read'],
      accessToken: 'tok-123',
    })
  })

  it('5.7 - flujo con requires_2fa: true redirige a /login/2fa', async () => {
    const user = userEvent.setup()

    vi.spyOn(apiModule.api, 'post').mockResolvedValueOnce({
      data: { requires_2fa: true, temp_token: 'temp-tok-abc' },
    })

    renderLoginPage()

    await user.type(screen.getByLabelText(/email/i), 'user@test.com')
    await user.type(screen.getByLabelText(/contraseña/i), 'password123')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(screen.getByText('Página 2FA')).toBeInTheDocument()
    })
  })

  it('5.9 - muestra error en credenciales inválidas (401)', async () => {
    const user = userEvent.setup()
    const error = { response: { status: 401 } }
    vi.spyOn(apiModule.api, 'post').mockRejectedValueOnce(error)

    renderLoginPage()

    await user.type(screen.getByLabelText(/email/i), 'bad@test.com')
    await user.type(screen.getByLabelText(/contraseña/i), 'wrongpass')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/credenciales inválidas/i)
    })
  })
})
