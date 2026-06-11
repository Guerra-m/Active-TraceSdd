import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { RequireAuth } from './RequireAuth'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import type { AuthUser } from '@/features/auth/context/AuthContext'

function mockUseAuth(user: AuthUser | null) {
  vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
    user,
    permissions: user ? ['alumnos:read'] : [],
    accessToken: user ? 'token' : null,
    setAuth: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  })
}

describe('RequireAuth', () => {
  it('4.3 - redirige a /login cuando no hay sesión', () => {
    mockUseAuth(null)

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <div>Dashboard</div>
              </RequireAuth>
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('4.4 - renderiza children cuando hay sesión válida', () => {
    mockUseAuth({
      id: '1',
      email: 'user@test.com',
      nombre: 'Test',
      rol: 'ALUMNO',
      tenant_id: 'tenant-1',
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <div>Dashboard Content</div>
              </RequireAuth>
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Dashboard Content')).toBeInTheDocument()
  })
})
