import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useAvisos,
  useCreateAviso,
  useUpdateAviso,
  useDeleteAviso,
  useAckAviso,
} from '../hooks/useAvisos'
import type { Aviso, AvisoAlcance } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  severidad: z.enum(['Info', 'Advertencia', 'Crítico']),
  inicio_en: z.string().min(1, 'La fecha de inicio es requerida'),
  fin_en: z.string().optional(),
  activo: z.boolean(),
  requiere_ack: z.boolean(),
})

type AvisoForm = z.infer<typeof avisoSchema>

const ALCANCE_LABELS: Record<AvisoAlcance, string> = {
  Global: 'Global',
  PorMateria: 'Por materia',
  PorCohorte: 'Por cohorte',
  PorRol: 'Por rol',
}

// ─── AvisoRow ─────────────────────────────────────────────────────────────────

function AvisoRow({
  aviso,
  onEdit,
}: {
  aviso: Aviso
  onEdit: (aviso: Aviso) => void
}) {
  const updateMutation = useUpdateAviso()
  const deleteMutation = useDeleteAviso()
  const ackMutation = useAckAviso()

  return (
    <tr className="border-b border-border">
      <td className="p-3 font-medium">{aviso.titulo}</td>
      <td className="p-3">{ALCANCE_LABELS[aviso.alcance]}</td>
      <td className="p-3 text-xs text-gray-500">{aviso.inicio_en.slice(0, 10)}</td>
      <td className="p-3">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            aviso.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
          }`}
        >
          {aviso.activo ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td className="p-3">
        <div className="flex gap-1">
          {!aviso.activo && (
            <button
              onClick={() =>
                updateMutation.mutate({ id: aviso.id, payload: { activo: true } })
              }
              disabled={updateMutation.isPending}
              className="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
            >
              Activar
            </button>
          )}
          {aviso.activo && (
            <button
              onClick={() =>
                updateMutation.mutate({ id: aviso.id, payload: { activo: false } })
              }
              disabled={updateMutation.isPending}
              className="rounded bg-yellow-600 px-2 py-1 text-xs text-white hover:bg-yellow-700 disabled:opacity-50"
            >
              Desactivar
            </button>
          )}
          {aviso.requiere_ack && (
            <button
              onClick={() => ackMutation.mutate(aviso.id)}
              disabled={ackMutation.isPending}
              className="rounded bg-indigo-600 px-2 py-1 text-xs text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              Confirmar lectura
            </button>
          )}
          <button
            onClick={() => onEdit(aviso)}
            className="rounded border border-border px-2 py-1 text-xs hover:bg-gray-50"
          >
            Editar
          </button>
          <button
            onClick={() => {
              if (confirm('¿Eliminar aviso?')) deleteMutation.mutate(aviso.id)
            }}
            className="rounded bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200"
          >
            Eliminar
          </button>
        </div>
      </td>
    </tr>
  )
}

// ─── AvisoModal ───────────────────────────────────────────────────────────────

function AvisoModal({
  aviso,
  onClose,
}: {
  aviso: Aviso | null
  onClose: () => void
}) {
  const createMutation = useCreateAviso()
  const updateMutation = useUpdateAviso()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AvisoForm>({
    resolver: zodResolver(avisoSchema),
    defaultValues: aviso
      ? {
          titulo: aviso.titulo,
          cuerpo: aviso.cuerpo,
          alcance: aviso.alcance,
          severidad: aviso.severidad,
          inicio_en: aviso.inicio_en.slice(0, 16),
          fin_en: aviso.fin_en?.slice(0, 16) ?? undefined,
          activo: aviso.activo,
          requiere_ack: aviso.requiere_ack,
        }
      : { alcance: 'Global', severidad: 'Info', activo: true, requiere_ack: false },
  })

  const isEditing = !!aviso
  const isPending = createMutation.isPending || updateMutation.isPending
  const isError = createMutation.isError || updateMutation.isError

  const onSubmit = (data: AvisoForm) => {
    if (isEditing) {
      updateMutation.mutate({ id: aviso.id, payload: data }, { onSuccess: onClose })
    } else {
      createMutation.mutate(data, { onSuccess: onClose })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">
          {isEditing ? 'Editar aviso' : 'Nuevo aviso'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="av-titulo">
              Título
            </label>
            <input
              id="av-titulo"
              {...register('titulo')}
              className="w-full rounded border border-border p-2"
            />
            {errors.titulo && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.titulo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="av-cuerpo">
              Cuerpo
            </label>
            <textarea
              id="av-cuerpo"
              {...register('cuerpo')}
              rows={4}
              className="w-full rounded border border-border p-2"
            />
            {errors.cuerpo && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.cuerpo.message}
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="av-alcance">
                Alcance
              </label>
              <select
                id="av-alcance"
                {...register('alcance')}
                className="w-full rounded border border-border p-2"
              >
                {Object.entries(ALCANCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="av-severidad">
                Severidad
              </label>
              <select
                id="av-severidad"
                {...register('severidad')}
                className="w-full rounded border border-border p-2"
              >
                <option value="Info">Info</option>
                <option value="Advertencia">Advertencia</option>
                <option value="Crítico">Crítico</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="av-inicio">
                Desde
              </label>
              <input
                id="av-inicio"
                type="datetime-local"
                {...register('inicio_en')}
                className="w-full rounded border border-border p-2"
              />
              {errors.inicio_en && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.inicio_en.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="av-fin">
                Hasta (opcional)
              </label>
              <input
                id="av-fin"
                type="datetime-local"
                {...register('fin_en')}
                className="w-full rounded border border-border p-2"
              />
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <input id="av-activo" type="checkbox" {...register('activo')} />
              <label className="text-sm" htmlFor="av-activo">
                Activo
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input id="av-ack" type="checkbox" {...register('requiere_ack')} />
              <label className="text-sm" htmlFor="av-ack">
                Requiere confirmación
              </label>
            </div>
          </div>
          {isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al guardar el aviso. Intentá de nuevo.
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
              disabled={isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function AvisosContent() {
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Aviso | null>(null)

  const { data, isLoading, isError } = useAvisos()
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
        Error al cargar los avisos. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Avisos</h1>
        <button
          onClick={() => {
            setEditTarget(null)
            setShowModal(true)
          }}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Nuevo aviso
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-500">No hay avisos.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Título</th>
                <th className="p-3 text-left">Alcance</th>
                <th className="p-3 text-left">Desde</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((aviso) => (
                <AvisoRow
                  key={aviso.id}
                  aviso={aviso}
                  onEdit={(a) => {
                    setEditTarget(a)
                    setShowModal(true)
                  }}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <AvisoModal
          aviso={editTarget}
          onClose={() => {
            setShowModal(false)
            setEditTarget(null)
          }}
        />
      )}
    </div>
  )
}

export function AvisosPage() {
  return (
    <RequirePermission permission="avisos:publicar">
      <AvisosContent />
    </RequirePermission>
  )
}
