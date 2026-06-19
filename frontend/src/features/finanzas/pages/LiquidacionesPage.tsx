import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Wallet,
  Gift,
  Clock,
  Timer,
  Download,
  SlidersHorizontal,
  ChevronRight,
  ChevronLeft,
  ChevronFirst,
  ChevronLast,
  MoreVertical,
  TrendingUp,
  CalendarClock,
} from 'lucide-react'
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

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

const AVATAR_COLORS = [
  'bg-[#d1e4fb] text-primary',
  'bg-[#cce2fc] text-secondary',
  'bg-[#ffddb7] text-[#362308]',
  'bg-[#b5c8df] text-primary',
]

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
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-4 border border-[#c4c6cd] rounded-lg">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
            Total Planilla
          </span>
          <Wallet className="w-5 h-5 text-primary" />
        </div>
        <p className="text-xl font-bold text-[#1b1c1d]">{fmt(total_general)}</p>
        <div className="flex items-center gap-1 text-green-600 text-xs mt-1">
          <TrendingUp className="w-3 h-3" />
          <span>General + NEXO + Facturantes</span>
        </div>
      </div>

      <div className="bg-white p-4 border border-[#c4c6cd] rounded-lg">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
            Total NEXO
          </span>
          <Gift className="w-5 h-5 text-primary" />
        </div>
        <p className="text-xl font-bold text-[#1b1c1d]">{fmt(total_nexo)}</p>
        <p className="text-[#43474c] text-xs mt-1">Liquidaciones NEXO</p>
      </div>

      <div className="bg-white p-4 border border-[#c4c6cd] rounded-lg">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
            Liquidaciones Abiertas
          </span>
          <Clock className="w-5 h-5 text-[#92400E]" />
        </div>
        <p className="text-xl font-bold text-[#1b1c1d]">{cantidad_liquidaciones}</p>
        <p className="text-[#43474c] text-xs mt-1">Pendientes de cierre</p>
      </div>

      <div className="bg-white p-4 border border-[#c4c6cd] rounded-lg">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
            Facturantes
          </span>
          <Timer className="w-5 h-5 text-primary" />
        </div>
        <p className="text-xl font-bold text-[#1b1c1d]">{fmt(total_facturantes)}</p>
        <p className="text-[#43474c] text-xs mt-1">Excluídos por factura</p>
      </div>
    </div>
  )
}

// ─── Fila de Liquidacion ──────────────────────────────────────────────────────

function LiquidacionRow({
  liquidacion,
  onCerrar,
  index,
}: {
  liquidacion: Liquidacion
  onCerrar: (id: string) => void
  index: number
}) {
  const estadoBadge: Record<LiquidacionEstado, string> = {
    Abierta: 'bg-[#FEF3C7] text-[#92400E]',
    Cerrada: 'bg-emerald-50 text-emerald-700',
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

  const avatarColor = AVATAR_COLORS[index % AVATAR_COLORS.length]

  return (
    <tr className="border-b border-[#c4c6cd] hover:bg-[#cce2fc]/20 transition-colors">
      <td className="px-3 py-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded flex items-center justify-center font-bold text-xs ${avatarColor}`}
          >
            {liquidacion.usuario_id.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="font-medium text-[#1b1c1d]">{tipoLabel}</p>
            <p className="text-xs text-[#43474c] font-mono">{liquidacion.usuario_id.slice(0, 8)}</p>
          </div>
        </div>
      </td>
      <td className="px-3 py-4 text-right font-mono text-sm">{fmt(liquidacion.monto_base)}</td>
      <td className="px-3 py-4 text-right font-mono text-sm text-blue-600">
        +{fmt(liquidacion.monto_plus)}
      </td>
      <td className="px-3 py-4 text-right font-bold text-primary">{fmt(liquidacion.total)}</td>
      <td className="px-3 py-4 text-center">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${estadoBadge[liquidacion.estado]}`}
        >
          {liquidacion.estado}
        </span>
      </td>
      <td className="px-3 py-4 text-center">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${tipoBadge}`}
        >
          {tipoLabel}
        </span>
      </td>
      <td className="px-3 py-4 text-right">
        {liquidacion.estado === 'Abierta' ? (
          <button
            onClick={() => onCerrar(liquidacion.id)}
            className="rounded bg-emerald-600 px-3 py-1 text-xs text-white hover:bg-emerald-700 font-medium"
          >
            Cerrar
          </button>
        ) : (
          <button className="text-[#74777d] hover:text-primary transition-colors">
            <MoreVertical className="w-4 h-4" />
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl border border-[#c4c6cd]">
        <h2 className="mb-4 text-lg font-semibold text-primary">Calcular liquidación</h2>

        {!resultado ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label
                className="mb-1 block text-sm font-medium text-[#1b1c1d]"
                htmlFor="cohorte_id"
              >
                ID de Cohorte
              </label>
              <input
                id="cohorte_id"
                {...register('cohorte_id')}
                className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="UUID de la cohorte"
              />
              {errors.cohorte_id && (
                <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                  {errors.cohorte_id.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="periodo">
                Período (YYYY-MM)
              </label>
              <input
                id="periodo"
                {...register('periodo')}
                className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="2024-03"
              />
              {errors.periodo && (
                <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                  {errors.periodo.message}
                </p>
              )}
            </div>
            {calcularMutation.isError && (
              <p role="alert" className="text-sm text-[#ba1a1a]">
                Error al calcular la liquidación. Intentá de nuevo.
              </p>
            )}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-[#c4c6cd] px-4 py-2 text-sm text-[#43474c] hover:bg-[#f5f3f4]"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={calcularMutation.isPending}
                className="rounded-lg bg-primary px-4 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
              >
                {calcularMutation.isPending ? 'Calculando...' : 'Calcular'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-[#43474c]">
              Liquidación calculada: {resultado.length} registros.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-[#f5f3f4] p-3 border border-[#c4c6cd]">
                <p className="text-xs text-[#43474c] font-bold uppercase tracking-[0.05em]">
                  Total general
                </p>
                <p className="font-bold text-primary text-lg">
                  {fmt(resultado.reduce((s, l) => s + l.total, 0))}
                </p>
              </div>
              <div className="rounded-lg bg-[#f5f3f4] p-3 border border-[#c4c6cd]">
                <p className="text-xs text-[#43474c] font-bold uppercase tracking-[0.05em]">
                  NEXO
                </p>
                <p className="font-bold text-primary text-lg">
                  {fmt(resultado.filter((l) => l.es_nexo).reduce((s, l) => s + l.total, 0))}
                </p>
              </div>
              <div className="rounded-lg bg-[#f5f3f4] p-3 border border-[#c4c6cd]">
                <p className="text-xs text-[#43474c] font-bold uppercase tracking-[0.05em]">
                  Facturantes
                </p>
                <p className="font-bold text-primary text-lg">
                  {fmt(
                    resultado
                      .filter((l) => l.excluido_por_factura)
                      .reduce((s, l) => s + l.total, 0),
                  )}
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setResultado(null)}
                className="rounded-lg border border-[#c4c6cd] px-4 py-2 text-sm text-[#43474c] hover:bg-[#f5f3f4]"
              >
                Volver
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700"
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
  const [tabActivo, setTabActivo] = useState<'all' | 'General' | 'NEXO' | 'Facturantes'>('all')

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

  const itemsFiltrados = items.filter((l) => {
    if (tabActivo === 'all') return true
    if (tabActivo === 'NEXO') return l.es_nexo
    if (tabActivo === 'Facturantes') return l.excluido_por_factura
    return !l.es_nexo && !l.excluido_por_factura
  })

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div
        role="alert"
        className="rounded-lg bg-[#ffdad6] p-4 text-[#93000a] border border-[#93000a]/20"
      >
        Error al cargar las liquidaciones. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-[#43474c] mb-1">
            <span>Finanzas</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-primary font-medium">Liquidaciones</span>
          </nav>
          <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-primary">
            Liquidaciones Mensuales
          </h1>
          <p className="text-[#43474c] text-sm">
            Período: {filtros.periodo ?? DEFAULT_PERIODO} · Planilla académica
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-[#74777d] bg-white text-primary rounded font-medium flex items-center gap-2 hover:bg-[#f5f3f4] transition-colors text-sm">
            <Download className="w-4 h-4" />
            Exportar PDF
          </button>
          <button
            onClick={() => setShowCalcular(true)}
            className="px-4 py-2 bg-primary text-white rounded font-medium flex items-center gap-2 hover:opacity-95 transition-opacity text-sm"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Calcular liquidación
          </button>
        </div>
      </div>

      {/* Filtros */}
      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-[#c4c6cd] bg-[#f5f3f4] p-4"
      >
        <div>
          <label
            className="mb-1 block text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
            htmlFor="f-cohorte"
          >
            Cohorte
          </label>
          <input
            id="f-cohorte"
            {...register('cohorte_id')}
            className="rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="UUID cohorte"
          />
        </div>
        <div>
          <label
            className="mb-1 block text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
            htmlFor="f-periodo"
          >
            Período
          </label>
          <input
            id="f-periodo"
            {...register('periodo')}
            className="rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="2024-03"
          />
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            className="rounded-lg border border-primary px-4 py-2 text-sm text-primary hover:bg-primary/5"
          >
            Filtrar
          </button>
        </div>
      </form>

      {/* KPI Cards */}
      {kpis && (
        <KPICards
          total_general={kpis.total_general}
          total_nexo={kpis.total_nexo}
          total_facturantes={kpis.total_facturantes}
          cantidad_liquidaciones={kpis.cantidad_liquidaciones}
        />
      )}

      {/* Tabla */}
      <div className="bg-white border border-[#c4c6cd] rounded-lg overflow-hidden">
        <div className="p-4 border-b border-[#c4c6cd] flex justify-between items-center bg-white">
          <div className="flex items-center gap-4">
            <h3 className="font-medium text-[#1b1c1d]">Detalle de liquidaciones</h3>
            <div className="flex gap-1">
              {(['all', 'General', 'NEXO', 'Facturantes'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setTabActivo(tab)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    tabActivo === tab
                      ? 'bg-primary text-white'
                      : 'bg-[#efedef] text-[#43474c] hover:bg-[#e4e2e3]'
                  }`}
                >
                  {tab === 'all' ? 'Todos' : tab}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#c4c6cd] bg-[#f5f3f4]">
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                  Usuario / ID
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-right">
                  Base
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-right">
                  Plus / Bonus
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-right">
                  Total
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-center">
                  Estado
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-center">
                  Tipo
                </th>
                <th className="px-3 py-2 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-right">
                  Acción
                </th>
              </tr>
            </thead>
            <tbody>
              {itemsFiltrados.map((liq, i) => (
                <LiquidacionRow
                  key={liq.id}
                  liquidacion={liq}
                  onCerrar={handleCerrar}
                  index={i}
                />
              ))}
              {itemsFiltrados.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-[#43474c]">
                    No hay liquidaciones para los filtros seleccionados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 bg-white border-t border-[#c4c6cd] flex justify-between items-center">
          <p className="text-xs text-[#43474c]">
            Mostrando {itemsFiltrados.length} de {items.length} liquidaciones
          </p>
          <div className="flex gap-1">
            <button className="p-1 hover:bg-[#efedef] rounded transition-colors">
              <ChevronFirst className="w-4 h-4 text-[#43474c]" />
            </button>
            <button className="p-1 hover:bg-[#efedef] rounded transition-colors">
              <ChevronLeft className="w-4 h-4 text-[#43474c]" />
            </button>
            <span className="px-3 flex items-center text-xs font-medium text-[#1b1c1d]">
              Página 1
            </span>
            <button className="p-1 hover:bg-[#efedef] rounded transition-colors">
              <ChevronRight className="w-4 h-4 text-[#43474c]" />
            </button>
            <button className="p-1 hover:bg-[#efedef] rounded transition-colors">
              <ChevronLast className="w-4 h-4 text-[#43474c]" />
            </button>
          </div>
        </div>
      </div>

      {/* Footer info cards */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-primary p-6 rounded-xl text-white relative overflow-hidden group">
          <div className="relative z-10">
            <h4 className="font-medium mb-1">Próximo ciclo de liquidación</h4>
            <p className="text-[#96a9be] text-sm mb-4">
              El próximo período comienza automáticamente. Asegurate de procesar todos los reclamos.
            </p>
            <button className="text-sm font-bold flex items-center gap-1 hover:underline">
              Ver calendario <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <CalendarClock className="absolute -right-4 -bottom-4 w-28 h-28 opacity-10 group-hover:scale-110 transition-transform duration-500" />
        </div>
        <div className="bg-[#e9e8e9] p-6 rounded-xl border border-[#c4c6cd] flex flex-col justify-center">
          <h4 className="font-medium mb-1 text-[#1b1c1d]">¿Necesitás reportes específicos?</h4>
          <p className="text-[#43474c] text-sm mb-4">
            Generá desglose detallado para auditoría o cumplimiento impositivo.
          </p>
          <div className="flex gap-3">
            <button className="text-primary font-bold text-sm hover:underline">
              Formularios impositivos
            </button>
            <div className="w-px h-4 bg-[#c4c6cd]" />
            <button className="text-primary font-bold text-sm hover:underline">
              Logs de auditoría
            </button>
          </div>
        </div>
      </div>

      {cerrarMutation.isError && (
        <p role="alert" className="text-sm text-[#ba1a1a]">
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
