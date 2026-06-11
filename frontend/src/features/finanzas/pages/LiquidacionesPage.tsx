import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useLiquidaciones,
  useLiquidacionKPIs,
  useCalcularLiquidacion,
  useCerrarLiquidacion,
} from '../hooks/useLiquidaciones'
import type { Liquidacion, LiquidacionEstado, LiquidacionFiltros } from '../types'

// ─── Schemas Zod ──────────────────────────────────────────────────────────────

const filtrosSchema = z.object({
  cohorte_id: z.string().optional(),
  periodo: z.string().optional(),
})

const calcularSchema = z.object({
  cohorte_id: z.string().min(1, 'Cohorte requerida'),
  periodo: z.string().min(7, 'Período requerido (YYYY-MM)'),
})

type FiltrosForm = z.infer<typeof filtrosSchema>
type CalcularForm = z.infer<typeof calcularSchema>

// ─── KPI Cards ────────────────────────────────────────────────────────────────

function KPICards({
  total_general,
  total_nexo,
  total_facturantes,
  cantidad_liquidaciones,
}: {
  total_general: number
  total_nexo: number
  total_facturantes: number
  cantidad_liquidaciones: number
}) {
  const fmt = (n: number) =>
    n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="rounded-lg border border-border bg-white p-4">
        <p className="text-sm text-gray-500">General</p>
        <p className="text-xl font-bold">{fmt(total_general)}</p>
      </div>
      <div className="rounded-lg border border-border bg-white p-4">
        <p className="text-sm text-gray-500">NEXO</p>
        <p className="text-xl font-bold">{fmt(total_nexo)}</p>
      </div>
      <div className="rounded-lg border border-border bg-white p-4">
        <p className="text-sm text-gray-500">Facturantes ({cantidad_liquidaciones})</p>
        <p className="text-xl font-bold">{fmt(total_facturantes)}</p>
      </div>
    </div>
  )
}

// ─── Fila de Liquidacion ──────────────────────────────────────────────────────

function LiquidacionRow({
  liquidacion,
  onCerrar,
}: {
  liquidacion: Liquidacion
  onCerrar: (id: string) => void
}) {
  const fmt = (n: number) =>
    n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

  const estadoBadge: Record<LiquidacionEstado, string> = {
    Abierta: 'bg-yellow-100 text-yellow-800',
    Cerrada: 'bg-green-100 text-green-800',
  }

  const tipoBadge = liquidacion.es_nexo
    ? 'bg-purple-100 text-purple-800'
    : liquidacion.excluido_por_factura
      ? 'bg-orange-100 text-orange-800'
      : 'bg-blue-100 text-blue-800'

  const tipoLabel = liquidacion.es_nexo
    ? 'NEXO'
    : liquidacion.excluido_por_factura
      ? 'Facturante'
      : 'General'

  return (
    <tr className="border-b border-border">
      <td className="p-3 font-mono text-xs text-gray-500">{liquidacion.usuario_id.slice(0, 8)}</td>
      <td className="p-3">
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${tipoBadge}`}>
          {tipoLabel}
        </span>
      </td>
      <td className="p-3">{fmt(liquidacion.monto_base)}</td>
      <td className="p-3">{fmt(liquidacion.monto_plus)}</td>
      <td className="p-3 font-semibold">{fmt(liquidacion.total)}</td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${estadoBadge[liquidacion.estado]}`}
        >
          {liquidacion.estado}
        </span>
      </td>
      <td className="p-3">
        {liquidacion.estado === 'Abierta' && (
          <button
            onClick={() => onCerrar(liquidacion.id)}
            className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700"
          >
            Cerrar
          </button>
        )}
      </td>
    </tr>
  )
}

// ─── Modal Calcular ───────────────────────────────────────────────────────────

function CalcularModal({ onClose }: { onClose: () => void }) {
  const [resultado, setResultado] = useState<Liquidacion[] | null>(null)
  const calcularMutation = useCalcularLiquidacion()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CalcularForm>({ resolver: zodResolver(calcularSchema) })

  const onSubmit = (data: CalcularForm) => {
    calcularMutation.mutate(data, {
      onSuccess: (liquidaciones) => setResultado(liquidaciones),
    })
  }

  const fmt = (n: number) =>
    n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Calcular liquidación</h2>

        {!resultado ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="cohorte_id">
                ID de Cohorte
              </label>
              <input
                id="cohorte_id"
                {...register('cohorte_id')}
                className="w-full rounded border border-border p-2"
                placeholder="UUID de la cohorte"
              />
              {errors.cohorte_id && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.cohorte_id.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="periodo">
                Período (YYYY-MM)
              </label>
              <input
                id="periodo"
                {...register('periodo')}
                className="w-full rounded border border-border p-2"
                placeholder="2024-03"
              />
              {errors.periodo && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errors.periodo.message}
                </p>
              )}
            </div>
            {calcularMutation.isError && (
              <p role="alert" className="text-sm text-red-600">
                Error al calcular la liquidación. Intentá de nuevo.
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
                disabled={calcularMutation.isPending}
                className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {calcularMutation.isPending ? 'Calculando...' : 'Calcular'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Liquidación calculada: {resultado.length} registros.
            </p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="rounded bg-gray-50 p-3">
                <p className="text-gray-500">Total general</p>
                <p className="font-bold">
                  {fmt(resultado.reduce((s, l) => s + l.total, 0))}
                </p>
              </div>
              <div className="rounded bg-gray-50 p-3">
                <p className="text-gray-500">NEXO</p>
                <p className="font-bold">
                  {fmt(resultado.filter((l) => l.es_nexo).reduce((s, l) => s + l.total, 0))}
                </p>
              </div>
              <div className="rounded bg-gray-50 p-3">
                <p className="text-gray-500">Facturantes</p>
                <p className="font-bold">
                  {fmt(resultado.filter((l) => l.excluido_por_factura).reduce((s, l) => s + l.total, 0))}
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setResultado(null)}
                className="rounded border border-border px-4 py-2 text-sm"
              >
                Volver
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
              >
                Cerrar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Content ─────────────────────────────────────────────────────────────────

const DEFAULT_PERIODO = new Date().toISOString().slice(0, 7)

function LiquidacionesContent() {
  const [filtros, setFiltros] = useState<LiquidacionFiltros>({ periodo: DEFAULT_PERIODO })
  const [showCalcular, setShowCalcular] = useState(false)

  const { data, isLoading, isError } = useLiquidaciones(filtros)
  const { data: kpis } = useLiquidacionKPIs(filtros)
  const cerrarMutation = useCerrarLiquidacion()
  const items = data ?? []

  const { register, handleSubmit } = useForm<FiltrosForm>({
    resolver: zodResolver(filtrosSchema),
    defaultValues: { periodo: DEFAULT_PERIODO },
  })

  const onFiltrar = (formData: FiltrosForm) => {
    setFiltros(formData)
  }

  const handleCerrar = (id: string) => {
    cerrarMutation.mutate(id)
  }

  const secciones = [
    { titulo: 'General', filtro: (l: Liquidacion) => !l.es_nexo && !l.excluido_por_factura },
    { titulo: 'NEXO', filtro: (l: Liquidacion) => l.es_nexo },
    { titulo: 'Facturantes', filtro: (l: Liquidacion) => l.excluido_por_factura },
  ]

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
        Error al cargar las liquidaciones. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Liquidaciones</h1>
        <button
          onClick={() => setShowCalcular(true)}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Calcular liquidación
        </button>
      </div>

      <form onSubmit={handleSubmit(onFiltrar)} className="flex gap-4 rounded-lg border border-border p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="f-cohorte">
            Cohorte
          </label>
          <input
            id="f-cohorte"
            {...register('cohorte_id')}
            className="rounded border border-border p-2 text-sm"
            placeholder="UUID cohorte"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="f-periodo">
            Período
          </label>
          <input
            id="f-periodo"
            {...register('periodo')}
            className="rounded border border-border p-2 text-sm"
            placeholder="2024-03"
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

      {kpis && (
        <KPICards
          total_general={kpis.total_general}
          total_nexo={kpis.total_nexo}
          total_facturantes={kpis.total_facturantes}
          cantidad_liquidaciones={kpis.cantidad_liquidaciones}
        />
      )}

      {secciones.map(({ titulo, filtro }) => {
        const seccionItems = items.filter(filtro)
        if (seccionItems.length === 0) return null

        return (
          <div key={titulo} className="overflow-x-auto rounded-lg border border-border">
            <h2 className="border-b border-border bg-gray-50 px-4 py-2 text-sm font-semibold">
              {titulo}
            </h2>
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-left">Usuario (ID)</th>
                  <th className="p-3 text-left">Tipo</th>
                  <th className="p-3 text-left">Base</th>
                  <th className="p-3 text-left">Plus</th>
                  <th className="p-3 text-left">Total</th>
                  <th className="p-3 text-left">Estado</th>
                  <th className="p-3 text-left">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {seccionItems.map((liq) => (
                  <LiquidacionRow key={liq.id} liquidacion={liq} onCerrar={handleCerrar} />
                ))}
              </tbody>
            </table>
          </div>
        )
      })}

      {items.length === 0 && (
        <p className="text-gray-500">No hay liquidaciones para los filtros seleccionados.</p>
      )}

      {cerrarMutation.isError && (
        <p role="alert" className="text-sm text-red-600">
          Error al cerrar la liquidación. Intentá de nuevo.
        </p>
      )}

      {showCalcular && <CalcularModal onClose={() => setShowCalcular(false)} />}
    </div>
  )
}

export function LiquidacionesPage() {
  return (
    <RequirePermission permission="liquidaciones:operar">
      <LiquidacionesContent />
    </RequirePermission>
  )
}
