import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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

// ─── Panel KPIs ───────────────────────────────────────────────────────────────

function PanelKPIs({ fecha_desde, fecha_hasta }: { fecha_desde?: string; fecha_hasta?: string }) {
  const { data: panel, isLoading } = useAuditPanel({ fecha_desde, fecha_hasta })

  if (isLoading) return <Spinner />
  if (!panel) return null

  return (
    <div className="space-y-4">
      {panel.acciones_por_dia.length > 0 && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="mb-2 font-semibold text-sm">Acciones por día</h3>
          <div className="flex gap-2 overflow-x-auto">
            {panel.acciones_por_dia.map((d) => (
              <div key={d.fecha} className="flex-shrink-0 rounded bg-blue-50 p-2 text-center text-xs">
                <div className="font-bold text-blue-800">{d.total}</div>
                <div className="text-gray-600">{d.fecha.slice(5)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {panel.por_actor.length > 0 && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="mb-2 font-semibold text-sm">Acciones por actor</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-1 text-left">Actor (ID)</th>
                <th className="py-1 text-left">Materia (ID)</th>
                <th className="py-1 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {panel.por_actor.map((c, i) => (
                <tr key={i} className="border-b border-border">
                  <td className="py-1 font-mono text-xs">{c.actor_id.slice(0, 8)}</td>
                  <td className="py-1 font-mono text-xs text-gray-500">
                    {c.materia_id ? c.materia_id.slice(0, 8) : '—'}
                  </td>
                  <td className="py-1 text-right font-medium">{c.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
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

  const { register, handleSubmit } = useForm<FiltrosForm>({
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
        Error al cargar el log de auditoría. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Panel de auditoría</h1>

      <PanelKPIs fecha_desde={filtros.fecha_desde} fecha_hasta={filtros.fecha_hasta} />

      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-border p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-desde">Desde</label>
          <input
            id="a-desde"
            type="date"
            {...register('fecha_desde')}
            className="rounded border border-border p-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-hasta">Hasta</label>
          <input
            id="a-hasta"
            type="date"
            {...register('fecha_hasta')}
            className="rounded border border-border p-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-materia">Materia (ID)</label>
          <input
            id="a-materia"
            {...register('materia_id')}
            className="rounded border border-border p-2 text-sm"
            placeholder="UUID"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-actor">Actor (ID)</label>
          <input
            id="a-actor"
            {...register('actor_id')}
            className="rounded border border-border p-2 text-sm"
            placeholder="UUID"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-accion">Acción</label>
          <input
            id="a-accion"
            {...register('accion')}
            className="rounded border border-border p-2 text-sm"
            placeholder="LOGIN, CREATE..."
          />
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            className="rounded border border-blue-600 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50"
          >
            Filtrar
          </button>
        </div>
      </form>

      {items.length === 0 ? (
        <p className="text-gray-500">No hay registros para los filtros seleccionados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-left">Actor (ID)</th>
                <th className="p-3 text-left">Acción</th>
                <th className="p-3 text-left">Detalle</th>
                <th className="p-3 text-left">IP</th>
              </tr>
            </thead>
            <tbody>
              {items.map((log) => (
                <tr key={log.id} className="border-b border-border">
                  <td className="p-3 text-gray-600">
                    {new Date(log.fecha_hora).toLocaleString('es-AR')}
                  </td>
                  <td className="p-3 font-mono text-xs">{log.actor_id.slice(0, 8)}</td>
                  <td className="p-3">
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium">
                      {log.accion}
                    </span>
                  </td>
                  <td className="p-3 text-gray-500 text-xs">
                    {log.detalle ? JSON.stringify(log.detalle).slice(0, 60) : '—'}
                  </td>
                  <td className="p-3 text-gray-600">{log.ip ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="text-sm text-gray-500">
        Total: {items.length} registros
      </div>
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
