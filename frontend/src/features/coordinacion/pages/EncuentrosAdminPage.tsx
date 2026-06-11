import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useEncuentrosAdmin,
  useCrearSlotsRecurrentes,
  useUpdateEncuentro,
} from '../hooks/useEncuentrosAdmin'
import type { EncuentroAdmin, EncuentroEstado } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const slotSchema = z.object({
  dia_semana: z.number({ invalid_type_error: 'Seleccione un día' }).min(0).max(6),
  hora: z.string().min(1, 'La hora es requerida'),
  recurrencia: z.enum(['semanal', 'quincenal']),
  periodo: z.string().min(1, 'El período es requerido'),
  tutor_id: z.string().min(1, 'El tutor es requerido'),
})

type SlotForm = z.infer<typeof slotSchema>

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const ESTADO_LABELS: Record<EncuentroEstado, string> = {
  programado: 'Programado',
  realizado: 'Realizado',
  cancelado: 'Cancelado',
  ausente: 'Ausente',
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
  const [fecha, setFecha] = useState(encuentro.fecha)
  const [hora, setHora] = useState(encuentro.hora)
  const [estado, setEstado] = useState<EncuentroEstado>(encuentro.estado)

  const handleSave = () => {
    updateMutation.mutate(
      { id: encuentro.id, payload: { fecha, hora, estado } },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Editar encuentro</h2>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="enc-fecha">
              Fecha
            </label>
            <input
              id="enc-fecha"
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              className="w-full rounded border border-border p-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="enc-hora">
              Hora
            </label>
            <input
              id="enc-hora"
              type="time"
              value={hora}
              onChange={(e) => setHora(e.target.value)}
              className="w-full rounded border border-border p-2"
            />
          </div>
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
              {Object.entries(ESTADO_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
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
  const slotMutation = useCrearSlotsRecurrentes()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SlotForm>({ resolver: zodResolver(slotSchema) })

  const onSubmit = (data: SlotForm) => {
    slotMutation.mutate(data, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Crear slots recurrentes</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="dia_semana">
              Día de la semana
            </label>
            <select
              id="dia_semana"
              {...register('dia_semana', { valueAsNumber: true })}
              className="w-full rounded border border-border p-2"
            >
              <option value="">Seleccionar día</option>
              {DIAS.map((dia, idx) => (
                <option key={dia} value={idx}>
                  {dia}
                </option>
              ))}
            </select>
            {errors.dia_semana && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.dia_semana.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="slot-hora">
              Hora
            </label>
            <input
              id="slot-hora"
              type="time"
              {...register('hora')}
              className="w-full rounded border border-border p-2"
            />
            {errors.hora && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.hora.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="recurrencia">
              Recurrencia
            </label>
            <select
              id="recurrencia"
              {...register('recurrencia')}
              className="w-full rounded border border-border p-2"
            >
              <option value="semanal">Semanal</option>
              <option value="quincenal">Quincenal</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="slot-periodo">
              Período
            </label>
            <input
              id="slot-periodo"
              {...register('periodo')}
              placeholder="Ej: 2024-1"
              className="w-full rounded border border-border p-2"
            />
            {errors.periodo && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.periodo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="tutor_id">
              ID Tutor
            </label>
            <input
              id="tutor_id"
              {...register('tutor_id')}
              className="w-full rounded border border-border p-2"
            />
            {errors.tutor_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.tutor_id.message}
              </p>
            )}
          </div>
          {slotMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al crear slots. Intentá de nuevo.
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
              {slotMutation.isPending ? 'Creando...' : 'Crear slots'}
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
          Crear slots recurrentes
        </button>
      </div>

      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay encuentros registrados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Alumno</th>
                <th className="p-3 text-left">Tutor</th>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-left">Hora</th>
                <th className="p-3 text-left">Tipo</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((enc) => (
                <tr key={enc.id} className="border-b border-border">
                  <td className="p-3">{enc.alumno_nombre}</td>
                  <td className="p-3">{enc.tutor_nombre}</td>
                  <td className="p-3">{enc.fecha}</td>
                  <td className="p-3">{enc.hora}</td>
                  <td className="p-3 capitalize">{enc.tipo}</td>
                  <td className="p-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        enc.estado === 'realizado'
                          ? 'bg-green-100 text-green-700'
                          : enc.estado === 'cancelado' || enc.estado === 'ausente'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {ESTADO_LABELS[enc.estado]}
                    </span>
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
