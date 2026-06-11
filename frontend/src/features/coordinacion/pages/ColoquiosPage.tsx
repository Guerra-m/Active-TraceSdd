import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useConvocatorias,
  useCreateConvocatoria,
  useImportarAlumnos,
  useMetricasColoquio,
} from '../hooks/useColoquios'
import type { Convocatoria, ConvocatoriaEstado } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const convocatoriaSchema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  cupo: z.number({ invalid_type_error: 'El cupo debe ser un número' }).min(1, 'El cupo debe ser mayor a 0'),
  descripcion: z.string().min(1, 'La descripción es requerida'),
})

const importarSchema = z.object({
  alumno_ids_raw: z.string().min(1, 'Seleccionar al menos un alumno'),
})

type ConvocatoriaForm = z.infer<typeof convocatoriaSchema>
type ImportarForm = z.infer<typeof importarSchema>

const ESTADO_LABELS: Record<ConvocatoriaEstado, string> = {
  abierta: 'Abierta',
  cerrada: 'Cerrada',
  finalizada: 'Finalizada',
}

// ─── MetricasPanel ────────────────────────────────────────────────────────────

function MetricasPanel({ convocatoriaId }: { convocatoriaId: string }) {
  const { data, isLoading } = useMetricasColoquio(convocatoriaId)

  if (isLoading) return <Spinner />

  return (
    <div className="mt-4 grid grid-cols-2 gap-3 rounded-lg border border-border p-4 sm:grid-cols-4">
      <div className="text-center">
        <p className="text-xs text-gray-500">Aprobados</p>
        <p className="text-2xl font-bold text-green-600">{data?.aprobados ?? '—'}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Desaprobados</p>
        <p className="text-2xl font-bold text-red-600">{data?.desaprobados ?? '—'}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Ausentes</p>
        <p className="text-2xl font-bold text-gray-600">{data?.ausentes ?? '—'}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Promedio</p>
        <p className="text-2xl font-bold text-blue-600">
          {data?.nota_promedio !== undefined ? data.nota_promedio.toFixed(1) : '—'}
        </p>
      </div>
    </div>
  )
}

// ─── ImportarModal ────────────────────────────────────────────────────────────

function ImportarModal({
  convocatoriaId,
  onClose,
}: {
  convocatoriaId: string
  onClose: () => void
}) {
  const importarMutation = useImportarAlumnos(convocatoriaId)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ImportarForm>({ resolver: zodResolver(importarSchema) })

  const onSubmit = (data: ImportarForm) => {
    const alumno_ids = data.alumno_ids_raw
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    importarMutation.mutate({ alumno_ids }, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Importar alumnos</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="alumno_ids_raw">
              IDs de alumnos (uno por línea)
            </label>
            <textarea
              id="alumno_ids_raw"
              {...register('alumno_ids_raw')}
              rows={6}
              placeholder="alumno-uuid-1&#10;alumno-uuid-2&#10;..."
              className="w-full rounded border border-border p-2 font-mono text-sm"
            />
            {errors.alumno_ids_raw && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.alumno_ids_raw.message}
              </p>
            )}
          </div>
          {importarMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al importar alumnos. Intentá de nuevo.
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
              disabled={importarMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {importarMutation.isPending ? 'Importando...' : 'Importar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── ConvocatoriaCard ─────────────────────────────────────────────────────────

function ConvocatoriaCard({ conv }: { conv: Convocatoria }) {
  const [showMetricas, setShowMetricas] = useState(false)
  const [showImportar, setShowImportar] = useState(false)

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{conv.materia_nombre}</h3>
          <p className="mt-1 text-sm text-gray-500">
            Fecha: {conv.fecha} · Cupo: {conv.inscriptos}/{conv.cupo}
          </p>
          {conv.descripcion && (
            <p className="mt-1 text-sm text-gray-400">{conv.descripcion}</p>
          )}
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            conv.estado === 'abierta'
              ? 'bg-green-100 text-green-700'
              : conv.estado === 'cerrada'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-gray-100 text-gray-600'
          }`}
        >
          {ESTADO_LABELS[conv.estado]}
        </span>
      </div>
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => setShowImportar(true)}
          className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50"
        >
          Importar alumnos
        </button>
        {conv.estado === 'finalizada' && (
          <button
            onClick={() => setShowMetricas((p) => !p)}
            className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50"
          >
            {showMetricas ? 'Ocultar métricas' : 'Ver métricas'}
          </button>
        )}
      </div>
      {showMetricas && <MetricasPanel convocatoriaId={conv.id} />}
      {showImportar && (
        <ImportarModal convocatoriaId={conv.id} onClose={() => setShowImportar(false)} />
      )}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function ColoquiosContent() {
  const { data, isLoading, isError } = useConvocatorias()
  const createMutation = useCreateConvocatoria()
  const [showForm, setShowForm] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ConvocatoriaForm>({ resolver: zodResolver(convocatoriaSchema) })

  const onSubmit = (data: ConvocatoriaForm) => {
    createMutation.mutate(data, {
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
        Error al cargar los coloquios. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Coloquios</h1>
        <button
          onClick={() => setShowForm((p) => !p)}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          {showForm ? 'Cancelar' : 'Nueva convocatoria'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-lg border border-border p-4 space-y-3"
        >
          <h2 className="font-medium">Nueva convocatoria</h2>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="materia_id">
              ID Materia
            </label>
            <input
              id="materia_id"
              {...register('materia_id')}
              className="w-full rounded border border-border p-2"
            />
            {errors.materia_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.materia_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="conv-fecha">
              Fecha
            </label>
            <input
              id="conv-fecha"
              type="date"
              {...register('fecha')}
              className="w-full rounded border border-border p-2"
            />
            {errors.fecha && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.fecha.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="cupo">
              Cupo
            </label>
            <input
              id="cupo"
              type="number"
              min={1}
              {...register('cupo', { valueAsNumber: true })}
              className="w-full rounded border border-border p-2"
            />
            {errors.cupo && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.cupo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="descripcion">
              Descripción
            </label>
            <textarea
              id="descripcion"
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
          {createMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al crear la convocatoria. Intentá de nuevo.
            </p>
          )}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creando...' : 'Crear convocatoria'}
          </button>
        </form>
      )}

      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay convocatorias.</p>
      ) : (
        <div className="space-y-3">
          {data?.items.map((conv) => (
            <ConvocatoriaCard key={conv.id} conv={conv} />
          ))}
        </div>
      )}
    </div>
  )
}

export function ColoquiosPage() {
  return (
    <RequirePermission permission="coloquios:read">
      <ColoquiosContent />
    </RequirePermission>
  )
}
