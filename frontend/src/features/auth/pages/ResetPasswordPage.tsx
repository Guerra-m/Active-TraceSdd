import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { api } from '@/shared/services/api'

const resetSchema = z
  .object({
    password: z
      .string()
      .min(8, 'La contraseña debe tener al menos 8 caracteres'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })

type ResetFormData = z.infer<typeof resetSchema>

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [apiError, setApiError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  })

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-muted px-4">
        <div className="w-full max-w-md rounded-xl bg-surface p-8 shadow-sm text-center">
          <p className="text-text-muted">Enlace inválido o expirado.</p>
          <Link to="/login/forgot" className="mt-4 inline-block text-sm text-brand-600">
            Solicitar nuevo enlace
          </Link>
        </div>
      </div>
    )
  }

  const onSubmit = async (data: ResetFormData) => {
    setApiError(null)
    setIsSubmitting(true)

    try {
      await api.post('/auth/reset', { token, password: data.password })
      navigate('/login', { replace: true })
    } catch {
      setApiError('El enlace expiró o es inválido. Solicitá uno nuevo.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-muted px-4">
      <div className="w-full max-w-md rounded-xl bg-surface p-8 shadow-sm">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-text">Nueva contraseña</h1>
          <p className="mt-1 text-sm text-text-muted">Ingresá tu nueva contraseña.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text">
              Nueva contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              {...register('password')}
              className="mt-1 block w-full rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-text placeholder-text-subtle focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            {errors.password && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.password.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-text">
              Confirmar contraseña
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              {...register('confirmPassword')}
              className="mt-1 block w-full rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-text placeholder-text-subtle focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            {errors.confirmPassword && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.confirmPassword.message}
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
            {isSubmitting ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </form>
      </div>
    </div>
  )
}
