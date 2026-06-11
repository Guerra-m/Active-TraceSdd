import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api, setAccessToken, setRefreshToken, getRefreshToken, registerForceLogout } from '@/shared/services/api'
import { Spinner } from '@/shared/components/Spinner'

// ─── Tipos ────────────────────────────────────────────────────────────────────
export interface AuthUser {
  id: string
  email: string
  nombre: string
  rol: string
  tenant_id: string
}

export interface AuthState {
  user: AuthUser | null
  permissions: string[]
  accessToken: string | null
}

interface AuthContextValue extends AuthState {
  setAuth: (state: AuthState) => void
  logout: () => Promise<void>
}

// ─── Context ──────────────────────────────────────────────────────────────────
const AuthContext = createContext<AuthContextValue | null>(null)

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  }
  return ctx
}

// ─── Provider ─────────────────────────────────────────────────────────────────
interface AuthProviderProps {
  children: ReactNode
}

interface RefreshResponse {
  access_token: string
  refresh_token?: string
  user: AuthUser
  permissions: string[]
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    permissions: [],
    accessToken: null,
  })
  const [isLoading, setIsLoading] = useState(true)

  const setAuth = useCallback((state: AuthState) => {
    setAuthState(state)
    setAccessToken(state.accessToken)
  }, [])

  const logout = useCallback(async () => {
    try {
      const rt = getRefreshToken()
      if (rt) {
        await api.post('/auth/logout', { refresh_token: rt })
      }
    } catch {
      // ignorar errores del logout remoto
    } finally {
      setRefreshToken(null)
      setAuth({ user: null, permissions: [], accessToken: null })
      window.location.href = '/login'
    }
  }, [setAuth])

  // Registrar logout forzado en el cliente API
  useEffect(() => {
    registerForceLogout(() => {
      setRefreshToken(null)
      setAuthState({ user: null, permissions: [], accessToken: null })
      setAccessToken(null)
    })
  }, [])

  // Silent refresh al montar
  useEffect(() => {
    let cancelled = false

    const silentRefresh = async () => {
      const storedToken = getRefreshToken()
      if (!storedToken) {
        setIsLoading(false)
        return
      }
      try {
        const { data } = await api.post<RefreshResponse>('/auth/refresh', { refresh_token: storedToken })
        if (!cancelled) {
          if (data.refresh_token) {
            setRefreshToken(data.refresh_token)
          }
          setAuth({
            user: data.user,
            permissions: data.permissions,
            accessToken: data.access_token,
          })
        }
      } catch {
        // Sesión expirada o no iniciada — dejamos como null
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void silentRefresh()

    return () => {
      cancelled = true
    }
  }, [setAuth])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ ...authState, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
