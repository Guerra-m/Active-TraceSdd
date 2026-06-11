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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Editar encuentro</h2>
        <p className="mb-3 text-sm text-gray-500">
          {encuentro.titulo} — {encuentro.fecha} {encuentro.hora}
        </p>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="enc-estado">
              Estado
            </label>
            <select
              id="enc-estado"
              value={estado}
              onChange={(e) => setEstado(e.target.value as EncuentroEstado)}
              className="w-full rounded border border-border p-2"
            >
              {(Object.keys(ESTADO_LABELS) as EncuentroEstado[]).map((v) => (
                <option key={v} value={v}>
                  {ESTADO_LABELS[v]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="enc-meet">
              URL Meet (opcional)
            </label>
            <input
              id="enc-meet"
              value={meetUrl}
              onChange={(e) => setMeetUrl(e.target.value)}
              className="w-full rounded border border-border p-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="enc-comentario">
              Comentario (opcional)
            </label>
            <textarea
              id="enc-comentario"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              rows={3}
              className="w-full rounded border border-border p-2"
            />
          </div>
          {updateMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al guardar. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="rounded border border-border px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateMutation.isPending ? 'Guardando...' : 'Guardar'}
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
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SlotForm>({
    resolver: zodResolver(slotSchema),
    defaultValues: { modo: 'recurrente' },
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Crear slot</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="sl-materia">
              ID Materia
            </label>
            <input
              id="sl-materia"
              {...register('materia_id')}
              className="w-full rounded border border-border p-2"
            />
            {errors.materia_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">{errors.materia_id.message}</p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="sl-titulo">
              Título
            </label>
            <input
              id="sl-titulo"
              {...register('titulo')}
              className="w-full rounded border border-border p-2"
            />
            {errors.titulo && (
              <p role="alert" className="mt-1 text-sm text-red-600">{errors.titulo.message}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="sl-hora">
                Hora
              </label>
              <input
                id="sl-hora"
                type="time"
                {...register('hora')}
                className="w-full rounded border border-border p-2"
              />
              {errors.hora && (
                <p role="alert" className="mt-1 text-sm text-red-600">{errors.hora.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="sl-modo">
                Modo
              </label>
              <select
                id="sl-modo"
                {...register('modo')}
                className="w-full rounded border border-border p-2"
              >
                <option value="recurrente">Recurrente</option>
                <option value="unico">Único</option>
              </select>
            </div>
          </div>

          {modo === 'recurrente' ? (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="sl-dia">
                  Día semana
                </label>
                <select
                  id="sl-dia"
                  {...register('dia_semana')}
                  className="w-full rounded border border-border p-2"
                >
                  <option value="">Seleccionar</option>
                  {['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                {errors.dia_semana && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errors.dia_semana.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="sl-semanas">
                  Semanas
                </label>
                <input
                  id="sl-semanas"
                  type="number"
                  min={1}
                  max={52}
                  {...register('cant_semanas')}
                  className="w-full rounded border border-border p-2"
                />
                {errors.cant_semanas && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errors.cant_semanas.message}</p>
                )}
              </div>
              <div className="col-span-2">
                <label className="mb-1 block text-sm font-medium" htmlFor="sl-inicio">
                  Fecha inicio
                </label>
                <input
                  id="sl-inicio"
                  type="date"
                  {...register('fecha_inicio')}
                  className="w-full rounded border border-border p-2"
                />
                {errors.fecha_inicio && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errors.fecha_inicio.message}</p>
                )}
              </div>
            </div>
          ) : (
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="sl-fecha-unica">
                Fecha
              </label>
              <input
                id="sl-fecha-unica"
                type="date"
                {...register('fecha_unica')}
                className="w-full rounded border border-border p-2"
              />
              {errors.fecha_unica && (
                <p role="alert" className="mt-1 text-sm text-red-600">{errors.fecha_unica.message}</p>
              )}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="sl-meet">
              URL Meet (opcional)
            </label>
            <input
              id="sl-meet"
              {...register('meet_url')}
              className="w-full rounded border border-border p-2"
            />
          </div>

          {slotMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al crear slot. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-border px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={slotMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {slotMutation.isPending ? 'Creando...' : 'Crear slot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
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
      <div role="alert" className="rounded bg-red-50 p-4 text-red-700">
        Error al cargar los encuentros. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Encuentros (Admin)</h1>
        <button
          onClick={() => setShowSlotModal(true)}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Crear slot
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-500">No hay encuentros registrados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Título</th>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-left">Hora</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Meet</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((enc) => (
                <tr key={enc.id} className="border-b border-border">
                  <td className="p-3 font-medium">{enc.titulo}</td>
                  <td className="p-3">{enc.fecha}</td>
                  <td className="p-3">{enc.hora}</td>
                  <td className="p-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        enc.estado === 'Realizado'
                          ? 'bg-green-100 text-green-700'
                          : enc.estado === 'Cancelado'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {ESTADO_LABELS[enc.estado]}
                    </span>
                  </td>
                  <td className="p-3">
                    {enc.meet_url ? (
                      <a href={enc.meet_url} target="_blank" rel="noreferrer" className="text-blue-600 underline text-xs">
                        Meet
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="p-3">
                    <button
                      onClick={() => setEditTarget(enc)}
                      className="rounded border border-border px-2 py-1 text-xs hover:bg-gray-50"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
