import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, Link } from 'react-router-dom'
import { api, setRefreshToken } from '@/shared/services/api'
import { useAuth } from '@/features/auth/context/AuthContext'
import type { AuthUser } from '@/features/auth/context/AuthContext'

const DEV_USERS = [
  { group: 'Staff',
    users: [
      { rol: 'Admin',            email: 'admin@trace.dev',                  password: 'admin123'      },
      { rol: 'Coordinador',      email: 'coord@trace.dev',                  password: 'coord123'      },
      { rol: 'Finanzas',         email: 'finanzas@trace.dev',               password: 'fin123'        },
    ]
  },
  { group: 'Docentes · ALGO1',
    users: [
      { rol: 'García (Profesor)',   email: 'rgarcia@trace.dev',             password: 'garcia123'     },
      { rol: 'Martínez (Tutor)',    email: 'cmartinez@trace.dev',           password: 'cmartinez123'  },
    ]
  },
  { group: 'Docentes · BD1',
    users: [
      { rol: 'Silva (Profesor)',    email: 'asilva@trace.dev',              password: 'silva123'      },
      { rol: 'López (Tutor)',       email: 'blopez@trace.dev',              password: 'blopez123'     },
    ]
  },
  { group: 'Alumnos · ALGO1',
    users: [
      { rol: 'Benitez (al día)',         email: 'facundo.benitez@alumno.utn.edu.ar',    password: 'alumno123' },
      { rol: 'Morales (atrasada)',        email: 'valentina.morales@alumno.utn.edu.ar',  password: 'alumno123' },
      { rol: 'Vargas (muy atrasada)',     email: 'florencia.vargas@alumno.utn.edu.ar',   password: 'alumno123' },
    ]
  },
]

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

type LoginFormData = z.infer<typeof loginSchema>

interface LoginResponse {
  requires_2fa: boolean
  temp_token?: string
  access_token?: string
  refresh_token?: string
  user?: AuthUser
  permissions?: string[]
}

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuth()
  const [apiError, setApiError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const fillCredentials = (email: string, password: string) => {
    setValue('email', email)
    setValue('password', password)
  }

  const quickLogin = async (email: string, password: string) => {
    setApiError(null)
    setIsSubmitting(true)
    try {
      const response = await api.post<LoginResponse>('/auth/login', { email, password })
      const result = response.data
      if (result.requires_2fa && result.temp_token) {
        navigate('/login/2fa', { state: { temp_token: result.temp_token } })
        return
      }
      if (result.access_token && result.user && result.permissions) {
        if (result.refresh_token) setRefreshToken(result.refresh_token)
        setAuth({ user: result.user, permissions: result.permissions, accessToken: result.access_token, asignacion: null })
        navigate('/dashboard', { replace: true })
      }
    } catch {
      setApiError('Error al iniciar sesión rápida.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const onSubmit = async (data: LoginFormData) => {
    setApiError(null)
    setIsSubmitting(true)

    try {
      const response = await api.post<LoginResponse>('/auth/login', data)
      const result = response.data

      if (result.requires_2fa && result.temp_token) {
        navigate('/login/2fa', { state: { temp_token: result.temp_token } })
        return
      }

      if (result.access_token && result.user && result.permissions) {
        if (result.refresh_token) {
          setRefreshToken(result.refresh_token)
        }
        setAuth({
          user: result.user,
          permissions: result.permissions,
          accessToken: result.access_token,
        })
        navigate('/dashboard', { replace: true })
      }
    } catch (err: unknown) {
      const error = err as { response?: { status: number } }
      if (error.response?.status === 401) {
        setApiError('Credenciales inválidas. Verificá tu email y contraseña.')
      } else {
        setApiError('Error de conexión. Intentá de nuevo más tarde.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-muted px-4">
      <div className="w-full max-w-md rounded-xl bg-surface p-8 shadow-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-text">activia-trace</h1>
          <p className="mt-1 text-sm text-text-muted">Iniciá sesión para continuar</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-text">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register('email')}
              className="mt-1 block w-full rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-text placeholder-text-subtle focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="tu@email.com"
            />
            {errors.email && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password')}
              className="mt-1 block w-full rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-text placeholder-text-subtle focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="••••••••"
            />
            {errors.password && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.password.message}
              </p>
            )}
          </div>

          {apiError && (
            <div role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {apiError}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {isSubmitting ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <Link to="/login/forgot" className="text-sm text-brand-600 hover:text-brand-700">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        {import.meta.env.DEV && (
          <div className="mt-6 rounded-lg border border-dashed border-surface-subtle bg-surface-muted p-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-subtle">
              Usuarios de prueba — click para ingresar
            </p>
            <div className="space-y-3">
              {DEV_USERS.map((group) => (
                <div key={group.group}>
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-text-subtle/60">
                    {group.group}
                  </p>
                  <div className="space-y-1">
                    {group.users.map((u) => (
                      <button
                        key={u.email}
                        type="button"
                        disabled={isSubmitting}
                        onClick={() => quickLogin(u.email, u.password)}
                        className="w-full rounded-md bg-surface px-3 py-1.5 text-left transition-colors hover:bg-surface-subtle disabled:opacity-50"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-text">{u.rol}</span>
                          <span className="font-mono text-[10px] text-text-subtle">{u.password}</span>
                        </div>
                        <span className="font-mono text-[10px] text-text-muted">{u.email}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
