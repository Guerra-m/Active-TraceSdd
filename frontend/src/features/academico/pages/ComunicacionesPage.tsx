import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEnviarComunicacion, useLotesComunicacion, useAprobarLote } from '../hooks/useComunicaciones'
import { useAuth } from '@/features/auth/context/AuthContext'
import type { EstadoLote } from '../types'

interface ComunicacionesPageProps {
  asignacionId: string
  materiaId: string
}

const schema = z.object({
  asunto_template: z.string().min(1, 'El asunto es obligatorio'),
  cuerpo_template: z.string().min(1, 'El mensaje es obligatorio'),
  criterio: z.enum(['atrasados', 'todos']),
})

type FormData = z.infer<typeof schema>

function estadoBadgeClass(estado: EstadoLote): string {
  switch (estado) {
    case 'Completado': return 'bg-green-100 text-green-800'
    case 'Cancelado': return 'bg-gray-100 text-gray-800'
    case 'Despachando': return 'bg-blue-100 text-blue-800'
    case 'PendienteAprobacion': return 'bg-orange-100 text-orange-800'
    default: return 'bg-yellow-100 text-yellow-800'
  }
}

export function ComunicacionesPage({ asignacionId, materiaId }: ComunicacionesPageProps) {
  const [step, setStep] = useState<'form' | 'preview' | 'lotes'>('form')
  const [previewData, setPreviewData] = useState<FormData | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { criterio: 'atrasados' },
  })

  const { permissions } = useAuth()
  const puedeAprobar = permissions.includes('comunicacion:aprobar')

  const enviar = useEnviarComunicacion()
  const aprobar = useAprobarLote()
  const { data: lotes, refetch: refetchLotes } = useLotesComunicacion()

  const sinContexto = !asignacionId || !materiaId

  function onShowPreview(data: FormData) {
    setPreviewData(data)
    setStep('preview')
  }

  function handleConfirmar() {
    if (!previewData) return
    enviar.mutate(
      {
        asignacion_id: asignacionId,
        materia_id: materiaId,
        criterio: previewData.criterio,
        asunto_template: previewData.asunto_template,
        cuerpo_template: previewData.cuerpo_template,
      },
      {
        onSuccess: () => {
          void refetchLotes()
          setStep('lotes')
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Comunicaciones a alumnos</h1>

      {sinContexto && (
        <p className="text-text-muted">No hay asignación seleccionada.</p>
      )}

      {!sinContexto && (
        <>
          {/* Paso 1: Formulario */}
          {step === 'form' && (
            <div className="max-w-lg space-y-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="asunto_template" className="text-sm font-medium text-text">Asunto</label>
                <input
                  id="asunto_template"
                  {...register('asunto_template')}
                  placeholder="Ej: Seguimiento académico — {{nombre}}"
                  className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {errors.asunto_template && (
                  <p className="text-sm text-red-600">{errors.asunto_template.message}</p>
                )}
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="cuerpo_template" className="text-sm font-medium text-text">Mensaje</label>
                <textarea
                  id="cuerpo_template"
                  rows={5}
                  {...register('cuerpo_template')}
                  placeholder="Ej: Hola {{nombre}}, te contactamos porque..."
                  className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {errors.cuerpo_template && (
                  <p className="text-sm text-red-600">{errors.cuerpo_template.message}</p>
                )}
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="criterio" className="text-sm font-medium text-text">Destinatarios</label>
                <select
                  id="criterio"
                  {...register('criterio')}
                  className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="atrasados">Solo alumnos atrasados</option>
                  <option value="todos">Todos los alumnos del padrón</option>
                </select>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleSubmit(onShowPreview)}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Ver preview
                </button>
                <button
                  type="button"
                  onClick={() => { void refetchLotes(); setStep('lotes') }}
                  className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle"
                >
                  Ver historial
                </button>
              </div>
            </div>
          )}

          {/* Paso 2: Preview */}
          {step === 'preview' && previewData && (
            <div className="max-w-lg space-y-4">
              <div className="rounded-lg border border-surface-subtle p-4 space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Preview</p>
                <p className="font-semibold text-text">{previewData.asunto_template}</p>
                <p className="text-sm text-text whitespace-pre-wrap">{previewData.cuerpo_template}</p>
                <p className="text-xs text-text-muted">
                  Destinatarios: {previewData.criterio === 'atrasados' ? 'Alumnos atrasados' : 'Todos los alumnos'}
                </p>
              </div>

              {enviar.isError && (
                <p className="text-sm text-red-600">Error al enviar. Verificá que existan destinatarios.</p>
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

          {/* Historial de lotes */}
          {step === 'lotes' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-text">Historial de envíos</h2>
                <button
                  type="button"
                  onClick={() => setStep('form')}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Nueva comunicación
                </button>
              </div>

              {!lotes || lotes.length === 0 ? (
                <p className="text-text-muted">No hay comunicaciones enviadas.</p>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-surface-subtle">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-muted">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium text-text-muted">Estado</th>
                        <th className="px-4 py-2 text-left font-medium text-text-muted">Mensajes</th>
                        <th className="px-4 py-2 text-left font-medium text-text-muted">Enviados</th>
                        <th className="px-4 py-2 text-left font-medium text-text-muted">Errores</th>
                        <th className="px-4 py-2 text-left font-medium text-text-muted">Fecha</th>
                        {puedeAprobar && (
                          <th className="px-4 py-2 text-left font-medium text-text-muted">Acción</th>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-subtle">
                      {lotes.map((lote) => (
                        <tr key={lote.id} className="hover:bg-surface-subtle">
                          <td className="px-4 py-2">
                            <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${estadoBadgeClass(lote.estado)}`}>
                              {lote.estado}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-text">{lote.total_mensajes}</td>
                          <td className="px-4 py-2 text-text">{lote.enviados}</td>
                          <td className="px-4 py-2 text-text">{lote.errores}</td>
                          <td className="px-4 py-2 text-text">
                            {new Date(lote.created_at).toLocaleDateString('es-AR')}
                          </td>
                          {puedeAprobar && (
                            <td className="px-4 py-2">
                              {lote.estado === 'PendienteAprobacion' && (
                                <button
                                  type="button"
                                  disabled={aprobar.isPending}
                                  onClick={() => aprobar.mutate(lote.id)}
                                  className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                                >
                                  Aprobar
                                </button>
                              )}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
