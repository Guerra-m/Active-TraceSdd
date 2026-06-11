import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from './AppLayout'
import * as AuthContextModule from '@/features/auth/context/AuthContext'
import type { AuthUser } from '@/features/auth/context/AuthContext'

function mockUseAuth(user: AuthUser | null, permissions: string[]) {
  vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
    user,
    permissions,
    accessToken: user ? 'token' : null,
    setAuth: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  })
}

describe('AppLayout', () => {
  it('6.4 - sidebar muestra solo ítems con permisos presentes', () => {
    mockUseAuth(
      { id: '1', email: 'u@t.com', nombre: 'Test User', rol: 'ALUMNO', tenant_id: 't1' },
      ['alumnos:read', 'materias:read'],
    )

    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    expect(screen.getByText('Alumnos')).toBeInTheDocument()
    expect(screen.getByText('Materias')).toBeInTheDocument()
    expect(screen.queryByText('Auditoría')).not.toBeInTheDocument()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
  })

  it('6.5 - topbar muestra nombre del usuario autenticado', () => {
    mockUseAuth(
      { id: '1', email: 'u@t.com', nombre: 'María García', rol: 'COORDINADOR', tenant_id: 't1' },
      ['alumnos:read'],
    )

    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    expect(screen.getByTestId('user-name')).toHaveTextContent('María García')
  })
})
