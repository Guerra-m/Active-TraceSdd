import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { TwoFactorPage } from './TwoFactorPage'
import * as AuthContextModule from '@/features/auth/context/AuthContext'

function mockUseAuth() {
  vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
    user: null,
    permissions: [],
    accessToken: null,
    setAuth: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  })
}

describe('TwoFactorPage', () => {
  it('5.8 - redirige a /login cuando no hay temp_token', () => {
    mockUseAuth()

    render(
      <MemoryRouter initialEntries={[{ pathname: '/login/2fa', state: null }]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/login/2fa" element={<TwoFactorPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })
})
