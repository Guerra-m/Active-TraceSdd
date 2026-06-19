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

// chip styling per estado
const ESTADO_CHIP: Record<TareaEstado, string> = {
  Pendiente: 'bg-surface-container-highest text-on-surface-variant',
  'En progreso': 'bg-amber-100 text-amber-800',
  Resuelta: 'bg-emerald-100 text-emerald-800',
  Cancelada: 'bg-surface-container-highest text-on-surface-variant',
}

// accent bar color per estado
const ESTADO_BAR: Record<TareaEstado, string> = {
  Pendiente: 'bg-primary/20',
  'En progreso': 'bg-amber-400',
  Resuelta: 'bg-emerald-500',
  Cancelada: 'bg-primary/20',
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
    <div className="flex-1 flex flex-col bg-surface-container-lowest overflow-hidden">
      {/* comment thread */}
      <div className="flex-1 p-6 overflow-y-auto max-h-80 space-y-6">
        <h4 className="text-label-caps font-label-caps text-secondary uppercase">
          Comentarios ({comentarios?.length ?? 0})
        </h4>
        {isLoading ? (
          <Spinner />
        ) : comentarios && comentarios.length > 0 ? (
          <div className="space-y-6">
            {comentarios.map((c) => (
              <div key={c.id} className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-container flex-shrink-0 flex items-center justify-center text-xs text-on-primary-container font-bold">
                  {c.autor_id.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-body-sm font-bold text-primary">{c.autor_id.slice(0, 8)}</span>
                  </div>
                  <p className="text-body-sm text-on-surface-variant">{c.texto}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-body-sm text-on-surface-variant">Sin comentarios aún.</p>
        )}
      </div>
      {/* comment input */}
      <div className="p-4 border-t border-outline-variant bg-surface-container-low">
        <form onSubmit={handleSubmit(onSubmit)} className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant rounded-lg px-1 pr-2">
          <input
            {...register('texto')}
            placeholder="Agregar comentario..."
            className="bg-transparent border-none focus:ring-0 text-body-sm flex-1 px-3 py-2 outline-none"
          />
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="text-primary bg-primary-container/10 p-1.5 rounded-md hover:bg-primary hover:text-on-primary transition-all disabled:opacity-50"
            aria-label="Enviar"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
        {errors.texto && (
          <p role="alert" className="mt-1 text-sm text-error">{errors.texto.message}</p>
        )}
      </div>
    </div>
  )
}

// ─── TareaCard ────────────────────────────────────────────────────────────────

function TareaCard({ tarea }: { tarea: Tarea }) {
  const [expanded, setExpanded] = useState(false)
  const cambiarEstadoMutation = useCambiarEstadoTarea()
  const isResuelta = tarea.estado === 'Resuelta'

  return (
    <div className="group flex items-stretch gap-4 p-4 border-b border-outline-variant hover:bg-surface-container-low transition-colors cursor-pointer">
      {/* accent bar */}
      <div className={`w-2 flex-shrink-0 self-stretch rounded-full opacity-60 group-hover:opacity-100 transition-opacity ${ESTADO_BAR[tarea.estado]}`} />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start mb-2">
          <h4 className={`text-title-sm font-title-sm text-on-surface group-hover:text-primary transition-colors ${isResuelta ? 'line-through opacity-60' : ''}`}>
            {tarea.descripcion}
          </h4>
          {/* status chip */}
          <span className={`shrink-0 ml-3 text-[11px] font-bold uppercase tracking-wide px-2 py-0.5 rounded ${ESTADO_CHIP[tarea.estado]}`}>
            {ESTADO_LABELS[tarea.estado]}
          </span>
        </div>
        <div className={`flex items-center gap-6 ${isResuelta ? 'opacity-60' : ''}`}>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-secondary-fixed flex items-center justify-center text-[10px] font-bold text-on-secondary-fixed">
              {tarea.asignado_a.slice(0, 2).toUpperCase()}
            </div>
            <span className="text-body-sm text-secondary font-mono text-data-mono">{tarea.asignado_a.slice(0, 12)}</span>
          </div>
        </div>
        {/* actions */}
        <div className="mt-3 flex items-center gap-3">
          <select
            value={tarea.estado}
            onChange={(e) =>
              cambiarEstadoMutation.mutate({ id: tarea.id, payload: { estado: e.target.value as TareaEstado } })
            }
            className="border border-outline-variant rounded-lg px-3 py-1 text-body-sm bg-surface text-on-surface focus:ring-1 focus:ring-primary outline-none"
            aria-label="Cambiar estado"
          >
            {(Object.keys(ESTADO_LABELS) as TareaEstado[]).map((value) => (
              <option key={value} value={value}>{ESTADO_LABELS[value]}</option>
            ))}
          </select>
          <button
            onClick={() => setExpanded((p) => !p)}
            className="text-body-sm text-secondary hover:text-primary font-medium transition-colors flex items-center gap-1"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            {expanded ? 'Ocultar comentarios' : 'Ver comentarios'}
          </button>
        </div>
        {expanded && <ComentariosPanel tareaId={tarea.id} />}
      </div>
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
      <div role="alert" className="rounded-lg bg-error-container/30 p-4 text-on-error-container">
        Error al cargar las tareas. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-1 text-body-sm text-secondary mb-1">
            <span>Departamento</span>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span>Coordinación</span>
          </div>
          <h2 className="text-display-lg font-display-lg text-primary">Gestión de Tareas</h2>
        </div>
        <button
          onClick={() => setShowForm((p) => !p)}
          className="bg-primary text-on-primary py-3 px-5 rounded-lg font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {showForm ? 'Cancelar' : 'Nueva Tarea'}
        </button>
      </div>

      {/* New task form */}
      {showForm && (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low">
            <h2 className="text-headline-md font-headline-md text-primary">Nueva tarea</h2>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="t-desc">
                DESCRIPCIÓN
              </label>
              <textarea
                id="t-desc"
                {...register('descripcion')}
                rows={3}
                placeholder="Describe la tarea a realizar..."
                className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md resize-none"
              />
              {errors.descripcion && (
                <p role="alert" className="text-sm text-error">{errors.descripcion.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="t-asignado">
                ASIGNADO A (ID USUARIO)
              </label>
              <input
                id="t-asignado"
                {...register('asignado_a')}
                placeholder="uuid del usuario..."
                className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary focus:border-primary bg-surface text-body-md font-mono"
              />
              {errors.asignado_a && (
                <p role="alert" className="text-sm text-error">{errors.asignado_a.message}</p>
              )}
            </div>
            {createMutation.isError && (
              <p role="alert" className="text-sm text-error">
                Error al crear la tarea. Intentá de nuevo.
              </p>
            )}
            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-primary text-on-primary px-6 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creando...' : 'Crear tarea'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Task list */}
      {items.length === 0 ? (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-12 text-center">
          <p className="text-on-surface-variant text-body-md">No hay tareas asignadas.</p>
        </div>
      ) : (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-6 py-3 border-b border-outline-variant bg-surface-container">
            <span className="text-label-caps font-label-caps text-on-surface-variant uppercase">{items.length} tareas</span>
          </div>
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
