import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, Link } from 'react-router-dom'
import { Mail, Lock, ArrowRight } from 'lucide-react'
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
    <div className="min-h-screen flex items-center justify-center bg-surface-container-low p-4">
      <main className="w-full max-w-[420px]">
        {/* Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 mb-1">
            <ArrowRight className="w-8 h-8 text-primary" strokeWidth={2.5} />
            <h1 className="text-[20px] leading-7 font-semibold tracking-tight text-primary">
              Activia-Trace
            </h1>
          </div>
          <p className="text-[13px] leading-[18px] text-on-surface-variant">
            Gestión Académica de Alto Rendimiento
          </p>
        </div>

        {/* Login Card */}
        <div
          className="bg-surface-container-lowest border border-outline-variant p-8 rounded-lg"
          style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1)' }}
        >
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
            {/* Email */}
            <div className="space-y-1">
              <label
                htmlFor="email"
                className="block text-[11px] leading-4 tracking-[0.05em] font-bold text-on-surface-variant uppercase"
              >
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-on-surface-variant pointer-events-none" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  placeholder="ejemplo@activia.edu"
                  className="w-full pl-11 pr-4 py-4 bg-surface border border-outline-variant rounded text-[14px] leading-5 text-on-surface placeholder:text-outline focus:border-primary-container focus:ring-1 focus:ring-primary-container outline-none transition-all"
                />
              </div>
              {errors.email && (
                <p role="alert" className="text-xs text-error">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label
                htmlFor="password"
                className="block text-[11px] leading-4 tracking-[0.05em] font-bold text-on-surface-variant uppercase"
              >
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-on-surface-variant pointer-events-none" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password')}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-4 bg-surface border border-outline-variant rounded text-[14px] leading-5 text-on-surface placeholder:text-outline focus:border-primary-container focus:ring-1 focus:ring-primary-container outline-none transition-all"
                />
              </div>
              {errors.password && (
                <p role="alert" className="text-xs text-error">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Remember & Forgot */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-outline-variant text-primary-container focus:ring-primary-container"
                />
                <span className="text-[13px] leading-[18px] text-on-surface-variant group-hover:text-on-surface transition-colors">
                  Recordarme
                </span>
              </label>
              <Link
                to="/login/forgot"
                className="text-[13px] leading-[18px] text-primary font-medium hover:underline transition-all"
              >
                Olvidé mi contraseña
              </Link>
            </div>

            {/* API Error */}
            {apiError && (
              <div role="alert" className="rounded-lg bg-error-container p-3 text-[13px] text-on-error-container">
                {apiError}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-primary-container text-on-primary py-4 text-[16px] leading-6 font-medium rounded-lg hover:bg-primary transition-all active:scale-[0.98] shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? 'Cargando...' : 'Iniciar sesión'}
              {!isSubmitting && <ArrowRight className="w-[18px] h-[18px]" />}
            </button>
          </form>

          {/* Footer within card */}
          <div className="mt-8 pt-6 border-t border-outline-variant flex flex-col items-center gap-4">
            <p className="text-[13px] leading-[18px] text-on-surface-variant">
              ¿Eres nuevo en la institución?
            </p>
            <button className="text-[11px] leading-4 tracking-[0.05em] font-bold text-primary border border-outline-variant px-6 py-2 rounded hover:bg-surface-container-high transition-colors uppercase">
              Solicitar acceso
            </button>
          </div>
        </div>

        {/* Page footer */}
        <footer className="mt-8 text-center">
          <p className="text-[13px] leading-[18px] text-outline mb-2">
            © 2024 Activia-Trace System. Todos los derechos reservados.
          </p>
          <div className="flex justify-center gap-4">
            <a href="#" className="text-[11px] leading-4 tracking-[0.05em] font-bold text-outline hover:text-on-surface-variant uppercase">
              Privacidad
            </a>
            <a href="#" className="text-[11px] leading-4 tracking-[0.05em] font-bold text-outline hover:text-on-surface-variant uppercase">
              Soporte
            </a>
          </div>
        </footer>

        {/* DEV: quick-fill panel */}
        {import.meta.env.DEV && (
          <div className="mt-6 rounded-lg border border-dashed border-outline-variant bg-surface-container-low p-4">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.05em] text-outline">
              Usuarios de prueba — click para ingresar
            </p>
            <div className="space-y-3">
              {DEV_USERS.map((group) => (
                <div key={group.group}>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.05em] text-outline/60">
                    {group.group}
                  </p>
                  <div className="space-y-1">
                    {group.users.map((u) => (
                      <button
                        key={u.email}
                        type="button"
                        disabled={isSubmitting}
                        onClick={() => quickLogin(u.email, u.password)}
                        className="w-full rounded-md bg-surface-container-lowest px-3 py-2 text-left transition-colors hover:bg-surface-container disabled:opacity-50"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-on-surface">{u.rol}</span>
                          <span className="font-mono text-[10px] text-outline">{u.password}</span>
                        </div>
                        <span className="font-mono text-[10px] text-on-surface-variant">{u.email}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
