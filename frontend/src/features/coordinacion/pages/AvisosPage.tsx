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
  usePublicarAviso,
  useAckAviso,
} from '../hooks/useAvisos'
import type { Aviso, AvisoEstado, AvisoScope } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  scope: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  fecha_expiracion: z.string().optional(),
  requiere_ack: z.boolean(),
})

type AvisoForm = z.infer<typeof avisoSchema>

const SCOPE_LABELS: Record<AvisoScope, string> = {
  Global: 'Global',
  PorMateria: 'Por materia',
  PorCohorte: 'Por cohorte',
  PorRol: 'Por rol',
}

const ESTADO_LABELS: Record<AvisoEstado, string> = {
  borrador: 'Borrador',
  publicado: 'Publicado',
  expirado: 'Expirado',
}

// ─── AvisoRow ─────────────────────────────────────────────────────────────────

function AvisoRow({
  aviso,
  onEdit,
}: {
  aviso: Aviso
  onEdit: (aviso: Aviso) => void
}) {
  const publicarMutation = usePublicarAviso()
  const deleteMutation = useDeleteAviso()
  const ackMutation = useAckAviso()

  return (
    <tr className="border-b border-border">
      <td className="p-3 font-medium">{aviso.titulo}</td>
      <td className="p-3">{SCOPE_LABELS[aviso.scope]}</td>
      <td className="p-3">{aviso.fecha_publicacion ?? '—'}</td>
      <td className="p-3">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            aviso.estado === 'publicado'
              ? 'bg-green-100 text-green-700'
              : aviso.estado === 'expirado'
                ? 'bg-gray-100 text-gray-600'
                : 'bg-yellow-100 text-yellow-700'
          }`}
        >
          {ESTADO_LABELS[aviso.estado]}
        </span>
      </td>
      <td className="p-3">
        <div className="flex gap-1">
          {aviso.estado === 'borrador' && (
            <button
              onClick={() => publicarMutation.mutate(aviso.id)}
              disabled={publicarMutation.isPending}
              className="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
            >
              Publicar
            </button>
          )}
          {aviso.requiere_ack && (
            <button
              onClick={() => ackMutation.mutate(aviso.id)}
              disabled={aviso.leido_por_mi || ackMutation.isPending}
              className="rounded bg-indigo-600 px-2 py-1 text-xs text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {aviso.leido_por_mi ? 'Leído' : 'Confirmar lectura'}
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
          scope: aviso.scope,
          fecha_expiracion: aviso.fecha_expiracion ?? undefined,
          requiere_ack: aviso.requiere_ack,
        }
      : { scope: 'Global', requiere_ack: false },
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
            <label className="mb-1 block text-sm font-medium" htmlFor="titulo">
              Título
            </label>
            <input
              id="titulo"
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
            <label className="mb-1 block text-sm font-medium" htmlFor="cuerpo">
              Cuerpo
            </label>
            <textarea
              id="cuerpo"
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
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="scope">
              Alcance
            </label>
            <select
              id="scope"
              {...register('scope')}
              className="w-full rounded border border-border p-2"
            >
              {Object.entries(SCOPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="fecha_expiracion">
              Fecha de expiración (opcional)
            </label>
            <input
              id="fecha_expiracion"
              type="date"
              {...register('fecha_expiracion')}
              className="w-full rounded border border-border p-2"
            />
          </div>
          <div className="flex items-center gap-2">
            <input id="requiere_ack" type="checkbox" {...register('requiere_ack')} />
            <label className="text-sm" htmlFor="requiere_ack">
              Requiere confirmación de lectura
            </label>
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
  const [filtroEstado, setFiltroEstado] = useState<AvisoEstado | undefined>(undefined)
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Aviso | null>(null)

  const { data, isLoading, isError } = useAvisos(
    filtroEstado ? { estado: filtroEstado } : undefined,
  )

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

      <div className="flex gap-2">
        {([undefined, 'publicado', 'borrador', 'expirado'] as (AvisoEstado | undefined)[]).map(
          (estado) => (
            <button
              key={String(estado)}
              onClick={() => setFiltroEstado(estado)}
              className={`rounded-full px-3 py-1 text-sm ${
                filtroEstado === estado
                  ? 'bg-blue-600 text-white'
                  : 'border border-border hover:bg-gray-50'
              }`}
            >
              {estado ? ESTADO_LABELS[estado] : 'Todos'}
            </button>
          ),
        )}
      </div>

      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay avisos.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Título</th>
                <th className="p-3 text-left">Alcance</th>
                <th className="p-3 text-left">Publicación</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((aviso) => (
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
