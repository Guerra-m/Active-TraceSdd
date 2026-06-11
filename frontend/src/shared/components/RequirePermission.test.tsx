import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RequirePermission } from './RequirePermission'
import * as AuthContextModule from '@/features/auth/context/AuthContext'

function mockPermissions(permissions: string[]) {
  vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
    user: { id: '1', email: 'u@t.com', nombre: 'U', rol: 'ALUMNO', tenant_id: 't1' },
    permissions,
    accessToken: 'token',
    setAuth: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  })
}

describe('RequirePermission', () => {
  it('4.5 - renderiza fallback cuando el usuario no tiene el permiso', () => {
    mockPermissions(['alumnos:read'])

    render(
      <RequirePermission permission="admin:write" fallback={<div>Sin acceso</div>}>
        <div>Contenido protegido</div>
      </RequirePermission>,
    )

    expect(screen.getByText('Sin acceso')).toBeInTheDocument()
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument()
  })

  it('renderiza children cuando el usuario tiene el permiso', () => {
    mockPermissions(['admin:write'])

    render(
      <RequirePermission permission="admin:write" fallback={<div>Sin acceso</div>}>
        <div>Contenido protegido</div>
      </RequirePermission>,
    )

    expect(screen.getByText('Contenido protegido')).toBeInTheDocument()
    expect(screen.queryByText('Sin acceso')).not.toBeInTheDocument()
  })
})
