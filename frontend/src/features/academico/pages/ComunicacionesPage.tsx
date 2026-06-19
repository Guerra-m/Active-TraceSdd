import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Send, X, PenSquare, Info } from 'lucide-react'
import { useEnviarComunicacion, useLotesComunicacion } from '../hooks/useComunicaciones'
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
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { criterio: 'atrasados' },
  })

  const cuerpoValue = watch('cuerpo_template', '')

  const enviar = useEnviarComunicacion()
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

  if (sinContexto) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="text-on-surface-variant">No hay asignación seleccionada.</p>
      </div>
    )
  }

  return (
    /* Modal-style canvas matching the HTML design */
    <div className="flex h-full items-stretch">
      <div
        className="bg-surface shadow-2xl border border-outline-variant rounded-xl w-full flex overflow-hidden"
        style={{ maxHeight: '800px' }}
      >
        {/* ── Left: Composition Form ── */}
        <div className="flex-[1.2] flex flex-col border-r border-outline-variant bg-surface-container-lowest">
          {/* Header */}
          <header className="h-16 px-6 flex items-center justify-between border-b border-outline-variant bg-surface shrink-0">
            <div className="flex items-center gap-2">
              <PenSquare className="h-5 w-5 text-primary" />
              <h2 className="text-title-sm font-title-sm text-primary">Nueva Comunicación</h2>
            </div>
            {step !== 'lotes' && (
              <button
                type="button"
                onClick={() => { void refetchLotes(); setStep('lotes') }}
                className="text-on-surface-variant hover:bg-surface-container-high rounded-full p-1 transition-colors"
                title="Ver historial"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </header>

          {/* ── Step: form ── */}
          {step === 'form' && (
            <>
              <form className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Destinatarios */}
                <div className="space-y-1">
                  <label htmlFor="criterio" className="block text-label-caps font-label-caps text-on-surface-variant uppercase">
                    DESTINATARIOS
                  </label>
                  <select
                    id="criterio"
                    {...register('criterio')}
                    className="w-full px-4 py-2 bg-surface border border-outline-variant focus:border-primary-container focus:ring-1 focus:ring-primary-container rounded-lg text-body-md transition-all outline-none"
                  >
                    <option value="atrasados">Solo alumnos atrasados</option>
                    <option value="todos">Todos los alumnos del padrón</option>
                  </select>
                </div>

                {/* Asunto */}
                <div className="space-y-1">
                  <label htmlFor="asunto_template" className="block text-label-caps font-label-caps text-on-surface-variant uppercase">
                    ASUNTO
                  </label>
                  <input
                    id="asunto_template"
                    {...register('asunto_template')}
                    placeholder="Ej: Seguimiento académico — {{nombre}}"
                    className="w-full px-4 py-2 bg-surface border border-outline-variant focus:border-primary-container focus:ring-1 focus:ring-primary-container rounded-lg text-body-md transition-all outline-none"
                  />
                  {errors.asunto_template && (
                    <p className="text-sm text-error">{errors.asunto_template.message}</p>
                  )}
                </div>

                {/* Cuerpo */}
                <div className="space-y-1">
                  <label htmlFor="cuerpo_template" className="block text-label-caps font-label-caps text-on-surface-variant uppercase">
                    CUERPO DEL MENSAJE
                  </label>
                  <div className="border border-outline-variant rounded-lg bg-surface overflow-hidden">
                    <div className="flex items-center gap-1 px-2 py-1 bg-surface-container-low border-b border-outline-variant">
                      <span className="text-body-sm text-on-surface-variant px-2 py-1">
                        Variables: <code className="font-mono bg-surface-container px-1 rounded text-xs">{'{{nombre}}'}</code>
                      </span>
                    </div>
                    <textarea
                      id="cuerpo_template"
                      rows={8}
                      {...register('cuerpo_template')}
                      placeholder="Hola {{nombre}}, te contactamos porque..."
                      className="w-full p-4 text-body-md border-none focus:ring-0 resize-none outline-none"
                    />
                  </div>
                  {errors.cuerpo_template && (
                    <p className="text-sm text-error">{errors.cuerpo_template.message}</p>
                  )}
                </div>
              </form>

              {/* Footer */}
              <footer className="h-20 px-6 flex items-center justify-between border-t border-outline-variant bg-surface shrink-0">
                <button
                  type="button"
                  onClick={() => { void refetchLotes(); setStep('lotes') }}
                  className="px-6 py-2 text-title-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg transition-colors"
                >
                  Ver historial
                </button>
                <button
                  type="button"
                  onClick={handleSubmit(onShowPreview)}
                  className="px-8 py-2 text-title-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg transition-all flex items-center gap-2 shadow-lg active:scale-95"
                >
                  Ver preview
                  <Send className="h-4 w-4" />
                </button>
              </footer>
            </>
          )}

          {/* ── Step: preview ── */}
          {step === 'preview' && previewData && (
            <>
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div className="rounded-lg border border-outline-variant p-6 space-y-3 bg-surface">
                  <p className="text-label-caps font-label-caps text-on-surface-variant uppercase">Vista previa</p>
                  <p className="text-title-sm font-title-sm text-primary">{previewData.asunto_template}</p>
                  <p className="text-body-md text-on-surface whitespace-pre-wrap">{previewData.cuerpo_template}</p>
                  <p className="text-body-sm text-on-surface-variant">
                    Destinatarios: {previewData.criterio === 'atrasados' ? 'Alumnos atrasados' : 'Todos los alumnos'}
                  </p>
                </div>
                {enviar.isError && (
                  <p className="text-sm text-error">Error al enviar. Verificá que existan destinatarios.</p>
                )}
              </div>
              <footer className="h-20 px-6 flex items-center justify-between border-t border-outline-variant bg-surface shrink-0">
                <button
                  type="button"
                  onClick={() => setStep('form')}
                  className="px-6 py-2 text-title-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleConfirmar}
                  disabled={enviar.isPending}
                  className="px-8 py-2 text-title-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg transition-all flex items-center gap-2 shadow-lg active:scale-95 disabled:opacity-50"
                >
                  {enviar.isPending ? 'Enviando…' : 'Confirmar envío'}
                  <Send className="h-4 w-4" />
                </button>
              </footer>
            </>
          )}

          {/* ── Step: lotes ── */}
          {step === 'lotes' && (
            <>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                <h2 className="text-headline-md font-headline-md text-primary">Historial de envíos</h2>
                {!lotes || lotes.length === 0 ? (
                  <p className="text-on-surface-variant text-body-md">No hay comunicaciones enviadas.</p>
                ) : (
                  <div className="overflow-x-auto rounded-lg border border-outline-variant">
                    <table className="w-full text-body-sm">
                      <thead className="bg-surface-container">
                        <tr>
                          <th className="px-4 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Estado</th>
                          <th className="px-4 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Mensajes</th>
                          <th className="px-4 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Enviados</th>
                          <th className="px-4 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Errores</th>
                          <th className="px-4 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Fecha</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant">
                        {lotes.map((lote) => (
                          <tr key={lote.id} className="hover:bg-surface-container-low transition-colors">
                            <td className="px-4 py-3">
                              <span className={`inline-flex rounded-full px-2 py-0.5 text-label-caps font-label-caps ${estadoBadgeClass(lote.estado)}`}>
                                {lote.estado}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-on-surface font-mono">{lote.total_mensajes}</td>
                            <td className="px-4 py-3 text-on-surface font-mono">{lote.enviados}</td>
                            <td className="px-4 py-3 text-on-surface font-mono">{lote.errores}</td>
                            <td className="px-4 py-3 text-on-surface-variant">
                              {new Date(lote.created_at).toLocaleDateString('es-AR')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
              <footer className="h-20 px-6 flex items-center justify-end border-t border-outline-variant bg-surface shrink-0">
                <button
                  type="button"
                  onClick={() => setStep('form')}
                  className="px-8 py-2 text-title-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg transition-all flex items-center gap-2 shadow-lg active:scale-95"
                >
                  Nueva comunicación
                  <Send className="h-4 w-4" />
                </button>
              </footer>
            </>
          )}
        </div>

        {/* ── Right: Live Preview (phone frame) ── */}
        {(step === 'form' || step === 'preview') && (
          <div className="flex-1 bg-surface-container flex flex-col">
            <header className="h-16 px-6 flex items-center border-b border-outline-variant bg-surface-container-high shrink-0">
              <span className="text-label-caps font-label-caps text-on-surface-variant uppercase">Vista del alumno</span>
            </header>
            <div className="flex-1 p-8 flex items-center justify-center overflow-hidden">
              {/* Phone frame */}
              <div
                className="w-full max-w-[280px] bg-white rounded-[36px] border-[8px] border-primary shadow-2xl overflow-hidden flex flex-col"
                style={{ aspectRatio: '9/16' }}
              >
                <div className="h-6 w-full flex justify-between items-center px-6 mt-3">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/20" />
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/20" />
                  </div>
                  <div className="text-[10px] font-bold text-primary/40">12:00</div>
                </div>
                <div className="px-4 py-5 flex-1 overflow-hidden">
                  <div className="mb-4">
                    <span className="bg-primary/5 text-primary text-[9px] font-bold px-2 py-0.5 rounded">INBOX</span>
                    <h3 className="text-primary font-bold text-base mt-1 leading-tight">Nueva comunicación</h3>
                    <p className="text-on-surface-variant text-[11px]">Del sistema académico</p>
                  </div>
                  <div className="bg-surface-container-low rounded-xl p-3 border border-outline-variant/30">
                    <p className="text-[12px] leading-relaxed text-on-surface line-clamp-6">
                      {cuerpoValue || 'El mensaje aparecerá aquí mientras escribís…'}
                    </p>
                  </div>
                  <div className="mt-4 flex flex-col gap-2">
                    <div className="h-8 w-full bg-primary rounded-lg flex items-center justify-center text-on-primary text-[11px] font-medium">
                      Responder
                    </div>
                    <div className="h-8 w-full border border-outline-variant rounded-lg flex items-center justify-center text-on-surface-variant text-[11px]">
                      Marcar como leído
                    </div>
                  </div>
                </div>
                <div className="h-10 w-full flex justify-center items-center gap-6 border-t border-outline-variant/10">
                  <div className="w-4 h-4 rounded-sm bg-outline/30" />
                  <div className="w-4 h-4 rounded-sm bg-primary" />
                  <div className="w-4 h-4 rounded-sm bg-outline/30" />
                </div>
              </div>
            </div>
            {/* Hint */}
            <div className="p-5 bg-surface-container-highest/50 border-t border-outline-variant shrink-0">
              <div className="flex items-start gap-3">
                <Info className="h-4 w-4 text-on-primary-container mt-0.5 shrink-0" />
                <p className="text-body-sm text-on-surface-variant italic">
                  Los alumnos recibirán el mensaje como notificación y por correo institucional.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
