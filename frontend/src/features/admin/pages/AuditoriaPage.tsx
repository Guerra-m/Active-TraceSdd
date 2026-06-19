import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Filter, X, ShieldCheck, Activity, Users } from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useAuditLogs, useAuditPanel } from '../hooks/useAuditoria'
import type { AuditLogFiltros } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const filtrosSchema = z.object({
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
  materia_id: z.string().optional(),
  actor_id: z.string().optional(),
  accion: z.string().optional(),
})

type FiltrosForm = z.infer<typeof filtrosSchema>

// ─── Action badge ─────────────────────────────────────────────────────────────

const ACTION_COLORS: Record<string, string> = {
  LOGIN:   'bg-emerald-100 text-emerald-700',
  LOGOUT:  'bg-slate-100  text-slate-600',
  CREATE:  'bg-blue-100   text-blue-700',
  UPDATE:  'bg-amber-100  text-amber-700',
  DELETE:  'bg-red-100    text-red-700',
  IMPORT:  'bg-purple-100 text-purple-700',
  EXPORT:  'bg-cyan-100   text-cyan-700',
}

function ActionBadge({ accion }: { accion: string }) {
  const colorClass = ACTION_COLORS[accion.toUpperCase()] ?? 'bg-surface-subtle text-text-muted'
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-bold uppercase tracking-wider border border-current/20 ${colorClass}`}>
      {accion}
    </span>
  )
}

// ─── Panel KPIs ───────────────────────────────────────────────────────────────

function PanelKPIs({ fecha_desde, fecha_hasta }: { fecha_desde?: string; fecha_hasta?: string }) {
  const { data: panel, isLoading } = useAuditPanel({ fecha_desde, fecha_hasta })

  if (isLoading) return <div className="flex items-center gap-2 py-2"><Spinner /><span className="text-sm text-text-muted">Cargando métricas…</span></div>
  if (!panel) return null

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {panel.acciones_por_dia.length > 0 && (
        <div className="rounded-xl border border-surface-subtle bg-surface p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50">
              <Activity className="h-4 w-4 text-brand-600" />
            </div>
            <h3 className="text-sm font-semibold text-text">Actividad por día</h3>
          </div>
          <div className="flex items-end gap-1.5 overflow-x-auto pb-1">
            {(() => {
              const max = Math.max(...panel.acciones_por_dia.map((d) => d.total), 1)
              return panel.acciones_por_dia.map((d) => (
                <div key={d.fecha} className="flex flex-col items-center gap-1" title={`${d.fecha}: ${d.total}`}>
                  <span className="text-[10px] font-semibold text-text-muted">{d.total}</span>
                  <div
                    className="w-6 min-h-[4px] rounded-t-sm bg-brand-400 transition-all"
                    style={{ height: `${Math.max(4, Math.round((d.total / max) * 56))}px` }}
                  />
                  <span className="text-[9px] text-text-subtle">{d.fecha.slice(5)}</span>
                </div>
              ))
            })()}
          </div>
        </div>
      )}

      {panel.por_actor.length > 0 && (
        <div className="rounded-xl border border-surface-subtle bg-surface p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-50">
              <Users className="h-4 w-4 text-purple-600" />
            </div>
            <h3 className="text-sm font-semibold text-text">Por actor</h3>
          </div>
          <div className="divide-y divide-surface-subtle">
            {panel.por_actor.map((c, i) => (
              <div key={i} className="flex items-center justify-between py-2 text-xs">
                <div>
                  <span className="font-mono text-text">{c.actor_id.slice(0, 8)}…</span>
                  {c.materia_id && (
                    <span className="ml-2 text-text-subtle">
                      mat: {c.materia_id.slice(0, 6)}…
                    </span>
                  )}
                </div>
                <span className="rounded-full bg-surface-subtle px-2 py-0.5 font-semibold text-text">
                  {c.total}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

function AuditoriaContent() {
  const [filtros, setFiltros] = useState<AuditLogFiltros>({})

  const { data, isLoading, isError } = useAuditLogs(filtros)
  const items = data ?? []

  const { register, handleSubmit, reset } = useForm<FiltrosForm>({
    resolver: zodResolver(filtrosSchema),
  })

  const onFiltrar = (formData: FiltrosForm) => {
    const newFiltros: AuditLogFiltros = {}
    if (formData.fecha_desde) newFiltros.fecha_desde = formData.fecha_desde
    if (formData.fecha_hasta) newFiltros.fecha_hasta = formData.fecha_hasta
    if (formData.materia_id) newFiltros.materia_id = formData.materia_id
    if (formData.actor_id) newFiltros.actor_id = formData.actor_id
    if (formData.accion) newFiltros.accion = formData.accion
    setFiltros(newFiltros)
  }

  const onLimpiar = () => {
    reset()
    setFiltros({})
  }

  const hasActiveFiltros = Object.values(filtros).some(Boolean)

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
          <ShieldCheck className="h-5 w-5 text-brand-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-text flex items-center gap-2">
            Registro de Auditoría
            <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="Registro inmutable">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </h2>
          <p className="text-sm text-text-muted">Log completo de acciones del tenant — historial inmutable</p>
        </div>
      </div>

      {/* Panel de métricas */}
      <PanelKPIs fecha_desde={filtros.fecha_desde} fecha_hasta={filtros.fecha_hasta} />

      {/* Filtros */}
      <div className="rounded-xl border border-surface-subtle bg-surface-muted p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <Filter className="h-4 w-4 text-text-muted" />
          <span className="text-sm font-medium text-text">Filtros</span>
          {hasActiveFiltros && (
            <span className="ml-auto rounded-full bg-brand-100 px-2 py-0.5 text-[11px] font-semibold text-brand-700">
              Activos
            </span>
          )}
        </div>
        <form onSubmit={handleSubmit(onFiltrar)} className="flex flex-wrap gap-3">
          {[
            { id: 'a-desde',   field: 'fecha_desde' as const, label: 'DESDE',       type: 'date', placeholder: '' },
            { id: 'a-hasta',   field: 'fecha_hasta' as const, label: 'HASTA',       type: 'date', placeholder: '' },
            { id: 'a-materia', field: 'materia_id'  as const, label: 'MATERIA ID',  type: 'text', placeholder: 'UUID' },
            { id: 'a-actor',   field: 'actor_id'    as const, label: 'ACTOR ID',    type: 'text', placeholder: 'UUID' },
            { id: 'a-accion',  field: 'accion'      as const, label: 'ACCIÓN',      type: 'text', placeholder: 'LOGIN, CREATE…' },
          ].map(({ id, field, label, type, placeholder }) => (
            <div key={id}>
              <label className="mb-1 block text-[11px] font-bold text-text-muted uppercase tracking-wider" htmlFor={id}>
                {label}
              </label>
              <input
                id={id}
                type={type}
                placeholder={placeholder}
                {...register(field)}
                className="rounded-lg border border-surface-subtle bg-surface px-3 py-2 text-sm text-text placeholder-text-subtle focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          ))}
          <div className="flex items-end gap-2">
            <button
              type="submit"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
            >
              Filtrar
            </button>
            {hasActiveFiltros && (
              <button
                type="button"
                onClick={onLimpiar}
                className="flex items-center gap-1.5 rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text-muted hover:bg-surface-subtle hover:text-text transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                Limpiar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Tabla */}
      {isLoading ? (
        <div className="flex items-center gap-3 py-6">
          <Spinner />
          <span className="text-sm text-text-muted">Cargando registros…</span>
        </div>
      ) : isError ? (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Error al cargar el log de auditoría. Intentá de nuevo.
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-surface-subtle bg-surface p-8 text-center">
          <ShieldCheck className="mx-auto mb-2 h-6 w-6 text-text-subtle" />
          <p className="text-sm text-text-muted">No hay registros para los filtros seleccionados.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-surface-subtle shadow-sm bg-surface">
            <table className="w-full border-collapse min-w-[900px]">
              <thead className="bg-surface-subtle border-b border-surface-subtle">
                <tr>
                  {[
                    { label: 'Timestamp',    cls: 'w-48' },
                    { label: 'Actor',        cls: 'w-40' },
                    { label: 'Acción',       cls: 'w-40' },
                    { label: 'Detalle',      cls: '' },
                    { label: 'IP',           cls: 'w-36' },
                  ].map(({ label, cls }) => (
                    <th key={label} className={`px-4 py-2 text-left text-[11px] font-bold text-text-muted uppercase tracking-wider ${cls}`}>
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-subtle">
                {items.map((log, idx) => (
                  <tr key={log.id} className={`hover:bg-surface-muted transition-colors ${idx % 2 === 1 ? 'bg-slate-50' : ''}`}>
                    <td className="px-4 py-3 font-mono text-xs text-text whitespace-nowrap">
                      {new Date(log.fecha_hora).toLocaleString('es-AR')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-text-muted" />
                        <span className="font-mono text-xs font-medium text-text">{log.actor_id.slice(0, 8)}…</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <ActionBadge accion={log.accion} />
                    </td>
                    <td className="px-4 py-3 text-xs text-text-muted max-w-xs truncate">
                      {log.detalle ? JSON.stringify(log.detalle).slice(0, 60) : '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-subtle">
                      {log.ip ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-text-subtle">
            Mostrando {items.length} registro{items.length !== 1 ? 's' : ''}
          </p>
        </>
      )}
    </div>
  )
}

export function AuditoriaPage() {
  return (
    <RequirePermission permission="auditoria:ver">
      <AuditoriaContent />
    </RequirePermission>
  )
}
