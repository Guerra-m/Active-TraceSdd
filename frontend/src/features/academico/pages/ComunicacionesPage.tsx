import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEnviarComunicacion, useEstadoComunicacion } from '../hooks/useComunicaciones'
import type { EstadoComunicacion } from '../types'

interface ComunicacionesPageProps {
  comisionId: string
}

const schema = z.object({
  asunto: z.string().min(1, 'El asunto es obligatorio'),
  cuerpo: z.string().min(1, 'El mensaje es obligatorio'),
  destinatarios: z.enum(['atrasados', 'todos']),
})

type FormData = z.infer<typeof schema>

function estadoBadgeClass(estado: EstadoComunicacion): string {
  switch (estado) {
    case 'ENVIADO': return 'bg-green-100 text-green-800'
    case 'FALLIDO': return 'bg-red-100 text-red-800'
    case 'CANCELADO': return 'bg-gray-100 text-gray-800'
    case 'ENVIANDO': return 'bg-blue-100 text-blue-800'
    default: return 'bg-yellow-100 text-yellow-800'
  }
}

export function ComunicacionesPage({ comisionId }: ComunicacionesPageProps) {
  const [step, setStep] = useState<'form' | 'preview' | 'tracking'>('form')
  const [previewData, setPreviewData] = useState<FormData | null>(null)
  const [comunicacionId, setComunicacionId] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { destinatarios: 'atrasados' },
  })

  const enviar = useEnviarComunicacion()
  const { data: estadoData } = useEstadoComunicacion(comunicacionId)

  function onShowPreview(data: FormData) {
    setPreviewData(data)
    setStep('preview')
  }

  function handleConfirmar() {
    if (!previewData) return
    enviar.mutate(
      {
        comision_id: comisionId,
        asunto: previewData.asunto,
        cuerpo: previewData.cuerpo,
        destinatarios: previewData.destinatarios,
      },
      {
        onSuccess: (resp) => {
          setComunicacionId(resp.id)
          setStep('tracking')
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Comunicaciones a atrasados</h1>

      {/* Paso 1: Formulario */}
      {step === 'form' && (
        <div className="max-w-lg space-y-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="asunto" className="text-sm font-medium text-text">Asunto</label>
            <input
              id="asunto"
              {...register('asunto')}
              className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            {errors.asunto && <p className="text-sm text-red-600">{errors.asunto.message}</p>}
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="cuerpo" className="text-sm font-medium text-text">Mensaje</label>
            <textarea
              id="cuerpo"
              rows={5}
              {...register('cuerpo')}
              className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            {errors.cuerpo && <p className="text-sm text-red-600">{errors.cuerpo.message}</p>}
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="destinatarios" className="text-sm font-medium text-text">Destinatarios</label>
            <select
              id="destinatarios"
              {...register('destinatarios')}
              className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="atrasados">Solo alumnos atrasados</option>
              <option value="todos">Todos los alumnos</option>
            </select>
          </div>

          <button
            type="button"
            onClick={handleSubmit(onShowPreview)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Ver preview
          </button>
        </div>
      )}

      {/* Paso 2: Preview */}
      {step === 'preview' && previewData && (
        <div className="max-w-lg space-y-4">
          <div className="rounded-lg border border-surface-subtle p-4 space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Preview</p>
            <p className="font-semibold text-text">{previewData.asunto}</p>
            <p className="text-sm text-text whitespace-pre-wrap">{previewData.cuerpo}</p>
            <p className="text-xs text-text-muted">
              Destinatarios: {previewData.destinatarios === 'atrasados' ? 'Alumnos atrasados' : 'Todos'}
            </p>
          </div>

          {enviar.isError && (
            <p className="text-sm text-red-600">Error al enviar. Intentá de nuevo.</p>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep('form')}
              className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirmar}
              disabled={enviar.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {enviar.isPending ? 'Enviando...' : 'Confirmar envío'}
            </button>
          </div>
        </div>
      )}

      {/* Paso 3: Tracking */}
      {step === 'tracking' && estadoData && (
        <div className="max-w-lg space-y-4">
          <p className="text-sm text-text-muted">
            Comunicación enviada. Estado en tiempo real:
          </p>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${estadoBadgeClass(estadoData.estado)}`}
            >
              {estadoData.estado}
            </span>
            {estadoData.motivo_fallo && (
              <span className="text-sm text-red-600">{estadoData.motivo_fallo}</span>
            )}
          </div>
          <button
            type="button"
            onClick={() => { setStep('form'); setComunicacionId(null) }}
            className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle"
          >
            Nueva comunicación
          </button>
        </div>
      )}
    </div>
  )
}
