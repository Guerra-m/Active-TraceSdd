import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useEncuentrosAdmin,
  useCrearSlot,
  useUpdateEncuentro,
} from '../hooks/useEncuentrosAdmin'
import { useMaterias } from '@/features/admin/hooks/useEstructura'
import type { EncuentroAdmin, EncuentroEstado } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const slotSchema = z
  .object({
    materia_id: z.string().min(1, 'La materia es requerida'),
    titulo: z.string().min(1, 'El título es requerido'),
    hora: z.string().min(1, 'La hora es requerida'),
    modo: z.enum(['recurrente', 'unico']),
    dia_semana: z.string().optional(),
    fecha_inicio: z.string().optional(),
    cant_semanas: z.coerce.number().optional(),
    fecha_unica: z.string().optional(),
    meet_url: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.modo === 'recurrente') {
      if (!data.dia_semana) ctx.addIssue({ code: 'custom', path: ['dia_semana'], message: 'Requerido' })
      if (!data.fecha_inicio) ctx.addIssue({ code: 'custom', path: ['fecha_inicio'], message: 'Requerido' })
      if (!data.cant_semanas) ctx.addIssue({ code: 'custom', path: ['cant_semanas'], message: 'Requerido' })
    } else {
      if (!data.fecha_unica) ctx.addIssue({ code: 'custom', path: ['fecha_unica'], message: 'Requerida' })
    }
  })

type SlotForm = z.infer<typeof slotSchema>

const ESTADO_LABELS: Record<EncuentroEstado, string> = {
  Programado: 'Programado',
  Realizado: 'Realizado',
  Cancelado: 'Cancelado',
}

// ─── EditEncuentroModal ───────────────────────────────────────────────────────

function EditEncuentroModal({
  encuentro,
  onClose,
}: {
  encuentro: EncuentroAdmin
  onClose: () => void
}) {
  const updateMutation = useUpdateEncuentro()
  const [estado, setEstado] = useState<EncuentroEstado>(encuentro.estado)
  const [meetUrl, setMeetUrl] = useState(encuentro.meet_url ?? '')
  const [comentario, setComentario] = useState(encuentro.comentario ?? '')

  const handleSave = () => {
    updateMutation.mutate(
      { id: encuentro.id, payload: { estado, meet_url: meetUrl || undefined, comentario: comentario || undefined } },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 backdrop-blur-sm p-6">
      <div className="bg-surface rounded-xl shadow-xl w-full max-w-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center">
          <h2 className="text-headline-md font-headline-md text-primary">Editar encuentro</h2>
        </div>
        <div className="p-6 space-y-4">
          <p className="text-body-sm text-on-surface-variant">
            {encuentro.titulo} — {encuentro.fecha} {encuentro.hora}
          </p>
          <div className="space-y-1">
            <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="enc-estado">
              ESTADO
            </label>
            <select
              id="enc-estado"
              value={estado}
              onChange={(e) => setEstado(e.target.value as EncuentroEstado)}
              className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md"
            >
              {(Object.keys(ESTADO_LABELS) as EncuentroEstado[]).map((v) => (
                <option key={v} value={v}>{ESTADO_LABELS[v]}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="enc-meet">
              LINK DE VIDEOCONFERENCIA (OPCIONAL)
            </label>
            <input
              id="enc-meet"
              value={meetUrl}
              onChange={(e) => setMeetUrl(e.target.value)}
              placeholder="https://meet.google.com/..."
              className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="enc-comentario">
              COMENTARIO (OPCIONAL)
            </label>
            <textarea
              id="enc-comentario"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              rows={3}
              className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md resize-none"
            />
          </div>
          {updateMutation.isError && (
            <p role="alert" className="text-sm text-error">
              Error al guardar. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-6 py-2 text-on-surface-variant font-medium hover:bg-surface-container rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="px-6 py-2 bg-primary text-on-primary font-medium rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {updateMutation.isPending ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── SlotModal ────────────────────────────────────────────────────────────────

function SlotModal({ onClose }: { onClose: () => void }) {
  const slotMutation = useCrearSlot()
  const { data: materias } = useMaterias()
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SlotForm>({
    resolver: zodResolver(slotSchema),
    defaultValues: { modo: 'unico' },
  })

  const modo = watch('modo')

  const onSubmit = (data: SlotForm) => {
    const payload = {
      materia_id: data.materia_id,
      titulo: data.titulo,
      hora: data.hora,
      meet_url: data.meet_url || undefined,
      ...(data.modo === 'recurrente'
        ? { dia_semana: data.dia_semana, fecha_inicio: data.fecha_inicio, cant_semanas: data.cant_semanas }
        : { fecha_unica: data.fecha_unica }),
    }
    slotMutation.mutate(payload, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="bg-surface rounded-xl shadow-xl w-full max-w-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center">
          <h4 className="text-headline-md font-headline-md text-primary">Agendar Encuentro</h4>
          <button
            type="button"
            onClick={onClose}
            className="p-1 hover:bg-surface-container rounded-full transition-colors"
          >
            <span className="sr-only">Cerrar</span>
            <svg className="h-5 w-5 text-on-surface-variant" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Título */}
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-titulo">
                TÍTULO DEL ENCUENTRO
              </label>
              <input
                id="sl-titulo"
                {...register('titulo')}
                placeholder="Ej: Clase Magistral de Ética"
                className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md"
              />
              {errors.titulo && (
                <p role="alert" className="text-sm text-error">{errors.titulo.message}</p>
              )}
            </div>

            {/* Materia */}
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-materia">
                MATERIA
              </label>
              <select
                id="sl-materia"
                {...register('materia_id')}
                className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md"
              >
                <option value="">Seleccioná una materia...</option>
                {(materias ?? []).map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre} ({m.codigo})</option>
                ))}
              </select>
              {errors.materia_id && (
                <p role="alert" className="text-sm text-error">{errors.materia_id.message}</p>
              )}
            </div>

            {/* Modo toggle */}
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase">
                MODO DE SESIÓN
              </label>
              <div className="flex gap-3">
                <label className={`flex-1 flex items-center justify-center py-2 px-4 border-2 rounded-lg font-medium cursor-pointer transition-all ${modo === 'unico' ? 'border-primary bg-primary/5 text-primary' : 'border-outline-variant text-on-surface-variant'}`}>
                  <input type="radio" {...register('modo')} value="unico" className="sr-only" />
                  Único
                </label>
                <label className={`flex-1 flex items-center justify-center py-2 px-4 border-2 rounded-lg font-medium cursor-pointer transition-all ${modo === 'recurrente' ? 'border-primary bg-primary/5 text-primary' : 'border-outline-variant text-on-surface-variant'}`}>
                  <input type="radio" {...register('modo')} value="recurrente" className="sr-only" />
                  Recurrente
                </label>
              </div>
            </div>

            {/* Campos para modo único */}
            {modo === 'unico' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-fecha-unica">
                    FECHA
                  </label>
                  <input
                    id="sl-fecha-unica"
                    type="date"
                    {...register('fecha_unica')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  />
                  {errors.fecha_unica && (
                    <p role="alert" className="text-sm text-error">{errors.fecha_unica.message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-hora">
                    HORA
                  </label>
                  <input
                    id="sl-hora"
                    type="time"
                    {...register('hora')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  />
                  {errors.hora && (
                    <p role="alert" className="text-sm text-error">{errors.hora.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Campos para modo recurrente */}
            {modo === 'recurrente' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-dia">
                    DÍA DE LA SEMANA
                  </label>
                  <select
                    id="sl-dia"
                    {...register('dia_semana')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  >
                    <option value="">Seleccionar</option>
                    {['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                  {errors.dia_semana && (
                    <p role="alert" className="text-sm text-error">{errors.dia_semana.message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-semanas">
                    NÚMERO DE SEMANAS
                  </label>
                  <input
                    id="sl-semanas"
                    type="number"
                    min={1}
                    max={52}
                    {...register('cant_semanas')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  />
                  {errors.cant_semanas && (
                    <p role="alert" className="text-sm text-error">{errors.cant_semanas.message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-inicio">
                    FECHA DE INICIO
                  </label>
                  <input
                    id="sl-inicio"
                    type="date"
                    {...register('fecha_inicio')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  />
                  {errors.fecha_inicio && (
                    <p role="alert" className="text-sm text-error">{errors.fecha_inicio.message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-hora-rec">
                    HORA
                  </label>
                  <input
                    id="sl-hora-rec"
                    type="time"
                    {...register('hora')}
                    className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                  />
                  {errors.hora && (
                    <p role="alert" className="text-sm text-error">{errors.hora.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Links */}
            <div className="border-t border-outline-variant pt-6 space-y-4">
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="sl-meet">
                  LINK DE VIDEOCONFERENCIA (OPCIONAL)
                </label>
                <input
                  id="sl-meet"
                  {...register('meet_url')}
                  placeholder="https://zoom.us/j/..."
                  type="url"
                  className="w-full border border-outline-variant rounded-lg p-3 bg-surface text-body-md"
                />
              </div>
            </div>

            {slotMutation.isError && (
              <p role="alert" className="text-sm text-error">
                Error al crear el encuentro. Intentá de nuevo.
              </p>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-8 py-2 text-on-surface-variant font-medium hover:bg-surface-container rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={slotMutation.isPending}
                className="px-8 py-2 bg-primary text-on-primary font-medium rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {slotMutation.isPending ? 'Creando...' : 'Crear Sesión'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function estadoEncuentroClass(estado: EncuentroEstado): string {
  switch (estado) {
    case 'Realizado': return 'bg-secondary-container text-on-secondary-container border-l-4 border-secondary'
    case 'Cancelado': return 'bg-error-container/30 text-on-error-container border-l-4 border-error'
    default: return 'bg-primary-container/10 border-l-4 border-primary'
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function EncuentrosAdminContent() {
  const { data, isLoading, isError } = useEncuentrosAdmin()
  const [editTarget, setEditTarget] = useState<EncuentroAdmin | null>(null)
  const [showSlotModal, setShowSlotModal] = useState(false)
  const items = data ?? []

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded-lg bg-error-container/30 p-4 text-on-error-container">
        Error al cargar los encuentros. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface">Agenda Académica</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">Administración de encuentros y sesiones</p>
        </div>
        <button
          onClick={() => setShowSlotModal(true)}
          className="bg-primary text-on-primary py-3 px-6 rounded-lg font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Encuentro
        </button>
      </div>

      {items.length === 0 ? (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-12 text-center">
          <p className="text-on-surface-variant text-body-md">No hay encuentros registrados.</p>
        </div>
      ) : (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low flex items-center justify-between">
            <h2 className="text-title-sm font-title-sm text-primary">Encuentros programados</h2>
            <span className="text-label-caps font-label-caps text-on-surface-variant">{items.length} encuentros</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-body-sm">
              <thead className="bg-surface-container border-b border-outline-variant">
                <tr>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Título</th>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Fecha</th>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Hora</th>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Estado</th>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Meet</th>
                  <th className="px-6 py-3 text-left text-label-caps font-label-caps text-on-surface-variant uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {items.map((enc) => (
                  <tr key={enc.id} className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-start px-3 py-1.5 rounded-r ${estadoEncuentroClass(enc.estado)}`}>
                        <span className="text-body-sm font-medium">{enc.titulo}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-on-surface font-mono text-data-mono">{enc.fecha}</td>
                    <td className="px-6 py-4 text-on-surface font-mono text-data-mono">{enc.hora}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`rounded-full px-3 py-1 text-label-caps font-label-caps ${
                          enc.estado === 'Realizado'
                            ? 'bg-secondary-container text-on-secondary-container'
                            : enc.estado === 'Cancelado'
                              ? 'bg-error-container text-on-error-container'
                              : 'bg-primary-fixed text-on-primary-fixed'
                        }`}
                      >
                        {ESTADO_LABELS[enc.estado]}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {enc.meet_url ? (
                        <a
                          href={enc.meet_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-secondary underline text-body-sm hover:text-primary transition-colors"
                        >
                          Abrir enlace
                        </a>
                      ) : (
                        <span className="text-on-surface-variant">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setEditTarget(enc)}
                        className="border border-outline-variant px-3 py-1.5 rounded-lg text-body-sm text-on-surface hover:bg-surface-container transition-colors"
                      >
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editTarget && (
        <EditEncuentroModal encuentro={editTarget} onClose={() => setEditTarget(null)} />
      )}

      {showSlotModal && <SlotModal onClose={() => setShowSlotModal(false)} />}
    </div>
  )
}

export function EncuentrosAdminPage() {
  return (
    <RequirePermission permission="encuentros:gestionar">
      <EncuentrosAdminContent />
    </RequirePermission>
  )
}
