import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useTareas,
  useCreateTarea,
  useCambiarEstadoTarea,
  useComentarios,
  useCreateComentario,
} from '../hooks/useTareas'
import type { Tarea, TareaEstado } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const createTareaSchema = z.object({
  descripcion: z.string().min(1, 'La descripción es requerida'),
  asignado_a: z.string().min(1, 'Debe ingresar el ID del usuario'),
})

const comentarioSchema = z.object({
  texto: z.string().min(1, 'El comentario no puede estar vacío'),
})

type CreateTareaForm = z.infer<typeof createTareaSchema>
type ComentarioForm = z.infer<typeof comentarioSchema>

const ESTADO_LABELS: Record<TareaEstado, string> = {
  Pendiente: 'Pendiente',
  'En progreso': 'En progreso',
  Resuelta: 'Resuelta',
  Cancelada: 'Cancelada',
}

const ESTADO_COLORS: Record<TareaEstado, string> = {
  Pendiente: 'bg-yellow-100 text-yellow-700',
  'En progreso': 'bg-blue-100 text-blue-700',
  Resuelta: 'bg-green-100 text-green-700',
  Cancelada: 'bg-gray-100 text-gray-600',
}

// ─── Comentarios Panel ────────────────────────────────────────────────────────

function ComentariosPanel({ tareaId }: { tareaId: string }) {
  const { data: comentarios, isLoading } = useComentarios(tareaId)
  const createMutation = useCreateComentario(tareaId)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ComentarioForm>({ resolver: zodResolver(comentarioSchema) })

  const onSubmit = (data: ComentarioForm) => {
    createMutation.mutate(data, { onSuccess: () => reset() })
  }

  return (
    <div className="mt-4 border-t border-border pt-4">
      <h3 className="mb-2 font-medium">Comentarios</h3>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-2">
          {comentarios?.map((c) => (
            <div key={c.id} className="rounded bg-gray-50 p-2 text-sm">
              <span className="font-mono text-xs text-gray-500">{c.autor_id.slice(0, 8)}:</span>{' '}
              {c.texto}
            </div>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit(onSubmit)} className="mt-3 flex gap-2">
        <input
          {...register('texto')}
          placeholder="Escribir comentario..."
          className="flex-1 rounded border border-border p-2 text-sm"
        />
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
      {errors.texto && (
        <p role="alert" className="mt-1 text-sm text-red-600">
          {errors.texto.message}
        </p>
      )}
    </div>
  )
}

// ─── TareaCard ────────────────────────────────────────────────────────────────

function TareaCard({ tarea }: { tarea: Tarea }) {
  const [expanded, setExpanded] = useState(false)
  const cambiarEstadoMutation = useCambiarEstadoTarea()

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{tarea.descripcion}</p>
          <p className="mt-1 font-mono text-xs text-gray-400">
            Asignado a: {tarea.asignado_a}
          </p>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${ESTADO_COLORS[tarea.estado]}`}>
          {ESTADO_LABELS[tarea.estado]}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <select
          value={tarea.estado}
          onChange={(e) =>
            cambiarEstadoMutation.mutate({ id: tarea.id, payload: { estado: e.target.value as TareaEstado } })
          }
          className="rounded border border-border p-1 text-sm"
          aria-label="Cambiar estado"
        >
          {(Object.keys(ESTADO_LABELS) as TareaEstado[]).map((value) => (
            <option key={value} value={value}>
              {ESTADO_LABELS[value]}
            </option>
          ))}
        </select>

        <button
          onClick={() => setExpanded((p) => !p)}
          className="text-sm text-blue-600 hover:underline"
        >
          {expanded ? 'Ocultar comentarios' : 'Ver comentarios'}
        </button>
      </div>

      {expanded && <ComentariosPanel tareaId={tarea.id} />}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function TareasContent() {
  const { data, isLoading, isError } = useTareas()
  const createMutation = useCreateTarea()
  const [showForm, setShowForm] = useState(false)
  const items = data ?? []

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateTareaForm>({ resolver: zodResolver(createTareaSchema) })

  const onSubmit = (formData: CreateTareaForm) => {
    createMutation.mutate(formData, {
      onSuccess: () => {
        reset()
        setShowForm(false)
      },
    })
  }

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
        Error al cargar las tareas. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tareas internas</h1>
        <button
          onClick={() => setShowForm((p) => !p)}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          {showForm ? 'Cancelar' : 'Nueva tarea'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-lg border border-border p-4 space-y-3"
        >
          <h2 className="font-medium">Nueva tarea</h2>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="t-desc">
              Descripción
            </label>
            <textarea
              id="t-desc"
              {...register('descripcion')}
              rows={3}
              className="w-full rounded border border-border p-2"
            />
            {errors.descripcion && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.descripcion.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="t-asignado">
              Asignado a (ID usuario)
            </label>
            <input
              id="t-asignado"
              {...register('asignado_a')}
              className="w-full rounded border border-border p-2"
            />
            {errors.asignado_a && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.asignado_a.message}
              </p>
            )}
          </div>
          {createMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al crear la tarea. Intentá de nuevo.
            </p>
          )}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creando...' : 'Crear tarea'}
          </button>
        </form>
      )}

      {items.length === 0 ? (
        <p className="text-gray-500">No hay tareas asignadas.</p>
      ) : (
        <div className="space-y-3">
          {items.map((tarea) => (
            <TareaCard key={tarea.id} tarea={tarea} />
          ))}
        </div>
      )}
    </div>
  )
}

export function TareasPage() {
  return (
    <RequirePermission permission="tareas:gestionar">
      <TareasContent />
    </RequirePermission>
  )
}
