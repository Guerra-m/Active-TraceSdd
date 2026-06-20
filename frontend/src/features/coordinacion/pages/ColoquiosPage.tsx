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
import { useMaterias, useCohortes, useCarreras } from '@/features/admin/hooks/useEstructura'
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

// ─── Tipo badge styling ───────────────────────────────────────────────────────

function tipoBadge(tipo: string): string {
  switch (tipo) {
    case 'Recuperatorio': return 'bg-tertiary-fixed-dim text-on-tertiary-fixed-variant'
    case 'Parcial': return 'bg-secondary-container text-on-secondary-container'
    case 'Coloquio': return 'bg-secondary-container text-on-secondary-container'
    default: return 'bg-surface-variant text-on-surface-variant'
  }
}

// ─── MetricasPanel ────────────────────────────────────────────────────────────

function MetricasPanel() {
  const { data, isLoading } = useMetricasColoquios()

  if (isLoading) return <Spinner />
  if (!data) return null

  return (
    <div className="bg-primary-container text-on-primary-container p-6 rounded-lg relative overflow-hidden">
      <div className="relative z-10">
        <h4 className="text-title-sm font-title-sm font-bold mb-1">Resumen Académico</h4>
        <p className="text-on-primary-container/80 text-body-sm mb-6">Métricas de convocatorias de evaluación activas.</p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-[10px] text-on-primary-container/70 uppercase font-bold mb-0.5">Convocados</p>
            <p className="text-white font-bold text-2xl leading-none">{data.total_convocados}</p>
          </div>
          <div>
            <p className="text-[10px] text-on-primary-container/70 uppercase font-bold mb-0.5">Instancias activas</p>
            <p className="text-white font-bold text-2xl leading-none">{data.instancias_activas}</p>
          </div>
          <div>
            <p className="text-[10px] text-on-primary-container/70 uppercase font-bold mb-0.5">Reservas activas</p>
            <p className="text-white font-bold text-2xl leading-none">{data.reservas_activas}</p>
          </div>
          <div>
            <p className="text-[10px] text-on-primary-container/70 uppercase font-bold mb-0.5">Notas registradas</p>
            <p className="text-white font-bold text-2xl leading-none">{data.notas_registradas}</p>
          </div>
        </div>
      </div>
      {/* decorative dots */}
      <div
        className="absolute top-0 right-0 w-32 h-32 opacity-10"
        style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '8px 8px' }}
      />
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 backdrop-blur-sm p-6">
      <div className="bg-surface w-full max-w-md rounded-lg shadow-xl border border-outline-variant overflow-hidden">
        <div className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-secondary-container text-on-secondary-container rounded-full flex items-center justify-center">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-headline-md font-headline-md text-primary">Importar alumnos</h3>
              <p className="text-on-surface-variant text-body-sm">Ingresá un UUID por línea.</p>
            </div>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1">
              <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="alumno_ids_raw">
                IDs DE ALUMNOS (uno por línea)
              </label>
              <textarea
                id="alumno_ids_raw"
                {...register('alumno_ids_raw')}
                rows={6}
                placeholder={"alumno-uuid-1\nalumno-uuid-2\n..."}
                className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-sm font-mono resize-none"
              />
              {errors.alumno_ids_raw && (
                <p role="alert" className="text-sm text-error">{errors.alumno_ids_raw.message}</p>
              )}
            </div>
            {importarMutation.isError && (
              <p role="alert" className="text-sm text-error">
                Error al importar alumnos. Intentá de nuevo.
              </p>
            )}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2 border border-outline text-on-surface font-medium rounded hover:bg-surface-container transition-all"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={importarMutation.isPending}
                className="flex-1 py-2 bg-primary text-on-primary font-medium rounded hover:bg-primary-container transition-all shadow-md disabled:opacity-50"
              >
                {importarMutation.isPending ? 'Importando...' : 'Importar'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ─── EvaluacionCard ───────────────────────────────────────────────────────────

function EvaluacionCard({ ev }: { ev: EvaluacionItem }) {
  const [showImportar, setShowImportar] = useState(false)
  const isUrgent = ev.cupos_por_dia - (ev.dias_disponibles ?? 0) <= 2

  return (
    <div className={`bg-surface border p-4 flex flex-col justify-between hover:border-primary transition-colors group ${isUrgent ? 'border-error-container bg-red-50/20' : 'border-outline-variant'}`}>
      <div>
        <div className="flex justify-between items-start mb-3">
          <span className={`px-2 py-0.5 text-label-caps font-label-caps rounded ${tipoBadge(ev.tipo)}`}>
            {ev.tipo.toUpperCase()}
          </span>
          <div className="flex items-center gap-1 text-primary font-medium">
            {isUrgent && (
              <svg className="h-4 w-4 text-error animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
            <span className="text-body-sm">{ev.cupos_por_dia} cupos/día</span>
          </div>
        </div>
        <h4 className="text-title-sm font-title-sm text-primary group-hover:text-primary transition-colors">
          {ev.instancia}
        </h4>
        <p className="text-on-surface-variant text-body-sm mt-1">Tipo: {ev.tipo}</p>
        <div className="mt-4 space-y-1">
          <div className="flex items-center gap-2 text-on-surface-variant">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-body-sm">{ev.dias_disponibles} días disponibles</span>
          </div>
          <div className="flex items-center gap-2 text-on-surface-variant">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span className="text-body-sm font-mono text-data-mono">{ev.materia_id.slice(0, 16)}…</span>
          </div>
        </div>
      </div>
      <button
        onClick={() => setShowImportar(true)}
        className="w-full mt-6 py-2 bg-primary text-on-primary rounded font-medium hover:bg-primary-container transition-all"
      >
        Importar alumnos
      </button>
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
  const { data: materias } = useMaterias()
  const { data: cohortes } = useCohortes()
  const { data: carreras } = useCarreras()
  const carreraMap = Object.fromEntries((carreras ?? []).map((c) => [c.id, c.nombre]))
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
      <div role="alert" className="rounded-lg bg-error-container/30 p-4 text-on-error-container">
        Error al cargar los coloquios. Intentá de nuevo.
      </div>
    )
  }

  const items = data ?? []

  return (
    <div className="space-y-6 pb-8">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-1 text-body-sm text-on-surface-variant mb-1">
          <span>Dashboard</span>
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span>Evaluaciones</span>
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-primary font-medium">Reservas</span>
        </div>
        <h2 className="text-display-lg font-display-lg text-primary">Coloquios y Evaluaciones</h2>
        <p className="text-on-surface-variant max-w-2xl mt-1 text-body-md">
          Administrá convocatorias de evaluación y gestioná el padrón de alumnos por instancia.
        </p>
      </div>

      {/* Metrics */}
      <MetricasPanel />

      {/* Grid: slots + sidebar */}
      <div className="grid grid-cols-12 gap-6">
        {/* Main: slot cards */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-headline-md font-headline-md text-primary">Convocatorias activas</h3>
            <button
              onClick={() => setShowForm((p) => !p)}
              className="border border-outline-variant rounded-lg px-4 py-2 text-body-sm bg-surface hover:bg-surface-container transition-all flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {showForm ? 'Cancelar' : 'Nueva convocatoria'}
            </button>
          </div>

          {/* New convocatoria form */}
          {showForm && (
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low">
                <h2 className="text-headline-md font-headline-md text-primary">Nueva convocatoria</h2>
              </div>
              <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="materia_id">
                      MATERIA
                    </label>
                    <select
                      id="materia_id"
                      {...register('materia_id')}
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
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
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="cohorte_id">
                      COHORTE
                    </label>
                    <select
                      id="cohorte_id"
                      {...register('cohorte_id')}
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
                    >
                      <option value="">Seleccioná una cohorte...</option>
                      {(cohortes ?? []).map((c) => (
                        <option key={c.id} value={c.id}>{carreraMap[c.carrera_id] ?? 'Carrera'} — {c.nombre} ({c.anio})</option>
                      ))}
                    </select>
                    {errors.cohorte_id && (
                      <p role="alert" className="text-sm text-error">{errors.cohorte_id.message}</p>
                    )}
                  </div>
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="tipo">
                      TIPO
                    </label>
                    <select
                      id="tipo"
                      {...register('tipo')}
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
                    >
                      <option value="Coloquio">Coloquio</option>
                      <option value="Parcial">Parcial</option>
                      <option value="TP">TP</option>
                      <option value="Recuperatorio">Recuperatorio</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="instancia">
                      INSTANCIA / DESCRIPCIÓN
                    </label>
                    <input
                      id="instancia"
                      {...register('instancia')}
                      placeholder="Ej: Coloquio 1er Cuatrimestre"
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
                    />
                    {errors.instancia && (
                      <p role="alert" className="text-sm text-error">{errors.instancia.message}</p>
                    )}
                  </div>
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="dias_disponibles">
                      DÍAS DISPONIBLES
                    </label>
                    <input
                      id="dias_disponibles"
                      type="number"
                      min={1}
                      {...register('dias_disponibles', { valueAsNumber: true })}
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
                    />
                    {errors.dias_disponibles && (
                      <p role="alert" className="text-sm text-error">{errors.dias_disponibles.message}</p>
                    )}
                  </div>
                  <div className="space-y-1">
                    <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="cupos_por_dia">
                      CUPOS POR DÍA
                    </label>
                    <input
                      id="cupos_por_dia"
                      type="number"
                      min={1}
                      {...register('cupos_por_dia', { valueAsNumber: true })}
                      className="w-full border border-outline-variant rounded-lg p-3 focus:ring-1 focus:ring-primary bg-surface text-body-md"
                    />
                    {errors.cupos_por_dia && (
                      <p role="alert" className="text-sm text-error">{errors.cupos_por_dia.message}</p>
                    )}
                  </div>
                </div>
                {createMutation.isError && (
                  <p role="alert" className="text-sm text-error">
                    Error al crear la convocatoria. Intentá de nuevo.
                  </p>
                )}
                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="bg-primary text-on-primary px-6 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {createMutation.isPending ? 'Creando...' : 'Crear convocatoria'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {items.length === 0 ? (
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-12 text-center">
              <p className="text-on-surface-variant text-body-md">No hay convocatorias activas.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {items.map((ev) => (
                <EvaluacionCard key={ev.id} ev={ev} />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar: info */}
        <div className="col-span-12 lg:col-span-4">
          <div className="bg-surface border border-outline-variant rounded shadow-sm overflow-hidden sticky top-24">
            <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low flex items-center justify-between">
              <h3 className="text-title-sm font-title-sm text-primary font-bold">Reservas activas</h3>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-body-sm text-on-surface-variant">
                Las convocatorias activas aparecen en la grilla principal. Usá el botón &ldquo;Importar alumnos&rdquo; en cada tarjeta para cargar el padrón habilitado.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-secondary-container inline-block" />
                  <span className="text-body-sm text-on-surface-variant">Parcial / Coloquio</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-tertiary-fixed-dim inline-block" />
                  <span className="text-body-sm text-on-surface-variant">Recuperatorio</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-error-container inline-block" />
                  <span className="text-body-sm text-on-surface-variant">Casi sin cupos</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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
