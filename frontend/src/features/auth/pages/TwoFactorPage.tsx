import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { ShieldCheck, ArrowRight, RefreshCw, Lock } from 'lucide-react'
import { api } from '@/shared/services/api'
import { useAuth } from '@/features/auth/context/AuthContext'
import type { AuthUser } from '@/features/auth/context/AuthContext'

const totpSchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d{6}$/, 'Solo dígitos'),
})

type TotpFormData = z.infer<typeof totpSchema>

interface TwoFactorResponse {
  access_token: string
  user: AuthUser
  permissions: string[]
}

export function TwoFactorPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { setAuth } = useAuth()
  const [apiError, setApiError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const tempToken = (location.state as { temp_token?: string } | null)?.temp_token

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TotpFormData>({
    resolver: zodResolver(totpSchema),
  })

  // Si no hay temp_token, redirigir a login
  if (!tempToken) {
    navigate('/login', { replace: true })
    return null
  }

  const onSubmit = async (data: TotpFormData) => {
    setApiError(null)
    setIsSubmitting(true)

    try {
      const response = await api.post<TwoFactorResponse>('/auth/2fa/verify', {
        code: data.code,
        temp_token: tempToken,
      })

      setAuth({
        user: response.data.user,
        permissions: response.data.permissions,
        accessToken: response.data.access_token,
      })
      navigate('/dashboard', { replace: true })
    } catch {
      setApiError('Código inválido. Verificá el código de tu app autenticadora.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-container-low p-4 overflow-hidden relative">
      {/* Atmospheric background decorations */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{ backgroundImage: 'radial-gradient(#e2e8f0 1px, transparent 1px)', backgroundSize: '24px 24px' }}
      />
      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-secondary-container/20 rounded-full blur-[100px] pointer-events-none" />

      <main className="w-full max-w-[440px] z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-primary rounded flex items-center justify-center mb-4">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-[20px] leading-7 font-semibold text-primary">Activia-Trace</h1>
        </div>

        {/* Verification Card */}
        <section className="bg-surface-container-lowest border border-outline-variant p-8 shadow-sm rounded-lg">
          <header className="text-center mb-8">
            <h2 className="text-[30px] leading-[38px] tracking-[-0.02em] font-semibold text-on-surface mb-2">
              Verificación de dos pasos
            </h2>
            <p className="text-[14px] leading-5 text-on-surface-variant max-w-[280px] mx-auto">
              Ingresá el código de 6 dígitos de tu app autenticadora
            </p>
          </header>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-8">
            {/* Single TOTP input — keeps RHF single-field contract */}
            <div>
              <label htmlFor="code" className="sr-only">
                Código TOTP
              </label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                {...register('code')}
                placeholder="000000"
                className="w-full text-center text-[20px] leading-7 font-bold text-primary bg-surface border border-outline-variant rounded-lg py-4 tracking-[0.4em] focus:outline-none transition-all"
                style={{ boxShadow: 'none' }}
                onFocus={(e) => (e.currentTarget.style.borderColor = '#2c3e50')}
                onBlur={(e) => (e.currentTarget.style.borderColor = '')}
              />
              {errors.code && (
                <p role="alert" className="mt-1 text-xs text-error text-center">
                  {errors.code.message}
                </p>
              )}
            </div>

            <div className="space-y-4">
              {/* API Error */}
              {apiError && (
                <div role="alert" className="rounded-lg bg-error-container p-3 text-[13px] text-on-error-container text-center">
                  {apiError}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 bg-primary-container text-white text-[16px] leading-6 font-medium rounded-lg hover:bg-primary transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <span>{isSubmitting ? 'Verificando...' : 'Verificar'}</span>
                {!isSubmitting && <ArrowRight className="w-[18px] h-[18px]" />}
              </button>

              <div className="flex flex-col items-center gap-2">
                <button
                  type="button"
                  className="text-[13px] leading-[18px] text-secondary hover:text-primary transition-colors flex items-center gap-1"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reenviar código
                </button>
                <Link
                  to="/login"
                  className="text-[13px] leading-[18px] text-on-surface-variant hover:underline"
                >
                  Volver al inicio de sesión
                </Link>
              </div>
            </div>
          </form>
        </section>

        {/* Footer */}
        <footer className="mt-8 text-center">
          <p className="text-[11px] leading-4 tracking-[0.05em] font-bold text-outline uppercase flex items-center justify-center gap-1">
            <Lock className="w-3 h-3" />
            Secure Academic Portal
          </p>
        </footer>
      </main>
    </div>
  )
}
