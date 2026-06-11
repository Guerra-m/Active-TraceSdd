import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useMonitor } from '../hooks/useMonitor'
import type { MonitorFiltros } from '../types'

// ─── Schema ───────────────────────────────────────────────────────────────────

const filtroSchema = z
  .object({
    desde: z.string().optional(),
    hasta: z.string().optional(),
  })
  .refine(
    (data) => {
      if (data.desde && data.hasta) {
        return new Date(data.desde) <= new Date(data.hasta)
      }
      return true
    },
    { message: 'La fecha desde no puede ser posterior a hasta', path: ['hasta'] },
  )

type FiltroForm = z.infer<typeof filtroSchema>

// ─── MetricCard ───────────────────────────────────────────────────────────────

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </div>
  )
}

// ─── MonitorContent ───────────────────────────────────────────────────────────

function MonitorContent() {
  const [filtros, setFiltros] = useState<MonitorFiltros | undefined>(undefined)
  const { data, isLoading, isError } = useMonitor(filtros)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FiltroForm>({ resolver: zodResolver(filtroSchema) })

  const onSubmit = (data: FiltroForm) => {
    setFiltros({
      desde: data.desde || undefined,
      hasta: data.hasta || undefined,
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Monitor de coordinación</h1>

      {/* Filtros de fecha */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-wrap items-end gap-4 rounded-lg border border-border p-4"
      >
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="desde">
            Desde
          </label>
          <input
            id="desde"
            type="date"
            {...register('desde')}
            className="rounded border border-border p-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="hasta">
            Hasta
          </label>
          <input
            id="hasta"
            type="date"
            {...register('hasta')}
            className="rounded border border-border p-2"
          />
          {errors.hasta && (
            <p role="alert" className="mt-1 text-sm text-red-600">
              {errors.hasta.message}
            </p>
          )}
        </div>
        <button
          type="submit"
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Aplicar filtro
        </button>
        {filtros && (
          <button
            type="button"
            onClick={() => setFiltros(undefined)}
            className="rounded border border-border px-4 py-2 text-sm hover:bg-gray-50"
          >
            Limpiar
          </button>
        )}
      </form>

      {/* Métricas */}
      {isLoading ? (
        <div className="flex justify-center p-8">
          <Spinner />
        </div>
      ) : isError ? (
        <div role="alert" className="rounded bg-red-50 p-4 text-red-700">
          Error al cargar el monitor. Intentá de nuevo.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <MetricCard label="Alumnos atrasados" value={data?.alumnos_atrasados ?? 0} />
            <MetricCard label="Entregas pendientes" value={data?.entregas_pendientes ?? 0} />
            <MetricCard label="Comunicaciones enviadas" value={data?.comunicaciones_enviadas ?? 0} />
            <MetricCard
              label="Tasa de contacto"
              value={`${Math.round((data?.tasa_contacto ?? 0) * 100)}%`}
            />
          </div>

          {/* Resumen por materia */}
          {data && data.resumen_por_materia.length > 0 && (
            <div>
              <h2 className="mb-3 text-lg font-semibold">Resumen por materia</h2>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="p-3 text-left">Materia</th>
                      <th className="p-3 text-left">Atrasados</th>
                      <th className="p-3 text-left">Al día</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.resumen_por_materia.map((row) => (
                      <tr key={row.materia_id} className="border-b border-border">
                        <td className="p-3 font-medium">{row.materia_nombre}</td>
                        <td className="p-3 text-red-600">{row.atrasados}</td>
                        <td className="p-3 text-green-600">{row.al_dia}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export function MonitorPage() {
  return (
    <RequirePermission permission="atrasados:ver">
      <MonitorContent />
    </RequirePermission>
  )
}
