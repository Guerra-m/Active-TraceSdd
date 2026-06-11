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
  desde: z.string().optional(),
  hasta: z.string().optional(),
  materia_id: z.string().optional(),
  usuario_id: z.string().optional(),
  accion: z.string().optional(),
})

type FiltrosForm = z.infer<typeof filtrosSchema>

// ─── Panel KPIs ───────────────────────────────────────────────────────────────

function PanelKPIs({ desde, hasta }: { desde?: string; hasta?: string }) {
  const { data: panel, isLoading } = useAuditPanel({ desde, hasta })

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
                <div className="font-bold text-blue-800">{d.count}</div>
                <div className="text-gray-600">{d.fecha.slice(5)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {panel.comunicaciones_por_docente.length > 0 && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="mb-2 font-semibold text-sm">Comunicaciones por docente</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-1 text-left">Docente</th>
                <th className="py-1 text-right text-green-700">Enviadas</th>
                <th className="py-1 text-right text-red-700">Fallidas</th>
              </tr>
            </thead>
            <tbody>
              {panel.comunicaciones_por_docente.map((c) => (
                <tr key={c.docente_nombre} className="border-b border-border">
                  <td className="py-1">{c.docente_nombre}</td>
                  <td className="py-1 text-right font-medium text-green-700">{c.enviadas}</td>
                  <td className="py-1 text-right font-medium text-red-700">{c.fallidas}</td>
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

  const { register, handleSubmit } = useForm<FiltrosForm>({
    resolver: zodResolver(filtrosSchema),
  })

  const onFiltrar = (data: FiltrosForm) => {
    const newFiltros: AuditLogFiltros = {}
    if (data.desde) newFiltros.desde = data.desde
    if (data.hasta) newFiltros.hasta = data.hasta
    if (data.materia_id) newFiltros.materia_id = data.materia_id
    if (data.usuario_id) newFiltros.usuario_id = data.usuario_id
    if (data.accion) newFiltros.accion = data.accion
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

      {/* Panel KPIs */}
      <PanelKPIs desde={filtros.desde} hasta={filtros.hasta} />

      {/* Filtros */}
      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-border p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-desde">Desde</label>
          <input
            id="a-desde"
            type="date"
            {...register('desde')}
            className="rounded border border-border p-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-hasta">Hasta</label>
          <input
            id="a-hasta"
            type="date"
            {...register('hasta')}
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
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="a-usuario">Usuario (ID)</label>
          <input
            id="a-usuario"
            {...register('usuario_id')}
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

      {/* Tabla de logs */}
      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay registros para los filtros seleccionados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-left">Usuario</th>
                <th className="p-3 text-left">Acción</th>
                <th className="p-3 text-left">Recurso</th>
                <th className="p-3 text-left">IP</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((log) => (
                <tr key={log.id} className="border-b border-border">
                  <td className="p-3 text-gray-600">
                    {new Date(log.creado_en).toLocaleString('es-AR')}
                  </td>
                  <td className="p-3 font-medium">{log.usuario_nombre}</td>
                  <td className="p-3">
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium">
                      {log.accion}
                    </span>
                  </td>
                  <td className="p-3">
                    {log.recurso}
                    {log.recurso_id && (
                      <span className="ml-1 text-gray-500 text-xs">({log.recurso_id.slice(0, 8)})</span>
                    )}
                  </td>
                  <td className="p-3 text-gray-600">{log.ip ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginación simple */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>Total: {data?.total ?? 0} registros</span>
        <span>Página {data?.page ?? 1} de {Math.ceil((data?.total ?? 0) / (data?.page_size ?? 20))}</span>
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
