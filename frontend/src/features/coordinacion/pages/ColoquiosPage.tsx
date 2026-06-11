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
  useMetricasColoquios,
} from '../hooks/useColoquios'
import type { EvaluacionItem } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const evaluacionSchema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  cohorte_id: z.string().min(1, 'La cohorte es requerida'),
  tipo: z.enum(['Parcial', 'TP', 'Coloquio', 'Recuperatorio']),
  instancia: z.string().min(1, 'La instancia es requerida'),
  dias_disponibles: z.number({ invalid_type_error: 'Debe ser un número' }).min(1),
  cupos_por_dia: z.number({ invalid_type_error: 'Debe ser un número' }).min(1),
})

const importarSchema = z.object({
  alumno_ids_raw: z.string().min(1, 'Ingresá al menos un ID'),
})

type EvaluacionForm = z.infer<typeof evaluacionSchema>
type ImportarForm = z.infer<typeof importarSchema>

// ─── MetricasPanel ────────────────────────────────────────────────────────────

function MetricasPanel() {
  const { data, isLoading } = useMetricasColoquios()

  if (isLoading) return <Spinner />
  if (!data) return null

  return (
    <div className="grid grid-cols-2 gap-3 rounded-lg border border-border p-4 sm:grid-cols-4">
      <div className="text-center">
        <p className="text-xs text-gray-500">Convocados</p>
        <p className="text-2xl font-bold text-blue-600">{data.total_convocados}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Instancias activas</p>
        <p className="text-2xl font-bold text-green-600">{data.instancias_activas}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Reservas activas</p>
        <p className="text-2xl font-bold text-yellow-600">{data.reservas_activas}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Notas registradas</p>
        <p className="text-2xl font-bold text-gray-600">{data.notas_registradas}</p>
      </div>
    </div>
  )
}

// ─── ImportarModal ────────────────────────────────────────────────────────────

function ImportarModal({
  evaluacionId,
  onClose,
}: {
  evaluacionId: string
  onClose: () => void
}) {
  const importarMutation = useImportarAlumnos(evaluacionId)
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

// ─── EvaluacionCard ───────────────────────────────────────────────────────────

function EvaluacionCard({ ev }: { ev: EvaluacionItem }) {
  const [showImportar, setShowImportar] = useState(false)

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{ev.instancia}</h3>
          <p className="mt-1 text-sm text-gray-500">
            Tipo: {ev.tipo} · Cupos/día: {ev.cupos_por_dia} · Días: {ev.dias_disponibles}
          </p>
          <p className="mt-1 font-mono text-xs text-gray-400">
            Materia: {ev.materia_id}
          </p>
        </div>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
          {ev.tipo}
        </span>
      </div>
      <div className="mt-3">
        <button
          onClick={() => setShowImportar(true)}
          className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50"
        >
          Importar alumnos
        </button>
      </div>
      {showImportar && (
        <ImportarModal evaluacionId={ev.id} onClose={() => setShowImportar(false)} />
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
  } = useForm<EvaluacionForm>({ resolver: zodResolver(evaluacionSchema) })

  const onSubmit = (formData: EvaluacionForm) => {
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
        Error al cargar los coloquios. Intentá de nuevo.
      </div>
    )
  }

  const items = data ?? []

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

      <MetricasPanel />

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-lg border border-border p-4 space-y-3"
        >
          <h2 className="font-medium">Nueva convocatoria</h2>
          <div className="grid grid-cols-2 gap-3">
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
              <label className="mb-1 block text-sm font-medium" htmlFor="cohorte_id">
                ID Cohorte
              </label>
              <input
                id="cohorte_id"
                {...register('cohorte_id')}
                className="w-full rounded border border-border p-2"
              />
              {errors.cohorte_id && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.cohorte_id.message}
                </p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="tipo">
                Tipo
              </label>
              <select
                id="tipo"
                {...register('tipo')}
                className="w-full rounded border border-border p-2"
              >
                <option value="Coloquio">Coloquio</option>
                <option value="Parcial">Parcial</option>
                <option value="TP">TP</option>
                <option value="Recuperatorio">Recuperatorio</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="instancia">
                Instancia / Descripción
              </label>
              <input
                id="instancia"
                {...register('instancia')}
                className="w-full rounded border border-border p-2"
                placeholder="Ej: Coloquio 1er Cuatrimestre"
              />
              {errors.instancia && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.instancia.message}
                </p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="dias_disponibles">
                Días disponibles
              </label>
              <input
                id="dias_disponibles"
                type="number"
                min={1}
                {...register('dias_disponibles', { valueAsNumber: true })}
                className="w-full rounded border border-border p-2"
              />
              {errors.dias_disponibles && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.dias_disponibles.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="cupos_por_dia">
                Cupos por día
              </label>
              <input
                id="cupos_por_dia"
                type="number"
                min={1}
                {...register('cupos_por_dia', { valueAsNumber: true })}
                className="w-full rounded border border-border p-2"
              />
              {errors.cupos_por_dia && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.cupos_por_dia.message}
                </p>
              )}
            </div>
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

      {items.length === 0 ? (
        <p className="text-gray-500">No hay convocatorias.</p>
      ) : (
        <div className="space-y-3">
          {items.map((ev) => (
            <EvaluacionCard key={ev.id} ev={ev} />
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
