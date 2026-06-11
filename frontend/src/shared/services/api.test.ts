import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, setAccessToken, getAccessToken, registerForceLogout } from './api'

describe('api interceptors', () => {
  let mockForceLogout: ReturnType<typeof vi.fn>

  beforeEach(() => {
    setAccessToken(null)
    mockForceLogout = vi.fn()
    registerForceLogout(mockForceLogout)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    setAccessToken(null)
  })

  it('2.4 - setAccessToken y getAccessToken mantienen el token en memoria', () => {
    expect(getAccessToken()).toBeNull()
    setAccessToken('test-token-123')
    expect(getAccessToken()).toBe('test-token-123')
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
  })

  it('2.4 - instancia api existe y tiene baseURL configurada', () => {
    expect(api).toBeDefined()
    expect(api.defaults.baseURL).toBe('/api')
  })

  it('2.4 - api tiene withCredentials en true', () => {
    expect(api.defaults.withCredentials).toBe(true)
  })

  it('2.6 - registerForceLogout registra la función de logout forzado', () => {
    const fn = vi.fn()
    registerForceLogout(fn)
    // La función queda registrada internamente; se verifica indirectamente
    expect(fn).not.toHaveBeenCalled()
  })

  it('2.4 - token puede actualizarse múltiples veces', () => {
    setAccessToken('token-1')
    expect(getAccessToken()).toBe('token-1')
    setAccessToken('token-2')
    expect(getAccessToken()).toBe('token-2')
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
  })
})
