import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, useLocation } from 'react-router-dom'
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
    <div className="flex min-h-screen items-center justify-center bg-surface-muted px-4">
      <div className="w-full max-w-md rounded-xl bg-surface p-8 shadow-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-text">Verificación de dos factores</h1>
          <p className="mt-1 text-sm text-text-muted">
            Ingresá el código de 6 dígitos de tu app autenticadora
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="code" className="block text-sm font-medium text-text">
              Código TOTP
            </label>
            <input
              id="code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              {...register('code')}
              className="mt-1 block w-full rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-center text-xl tracking-widest text-text focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="000000"
            />
            {errors.code && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.code.message}
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
            {isSubmitting ? 'Verificando...' : 'Verificar'}
          </button>
        </form>
      </div>
    </div>
  )
}
