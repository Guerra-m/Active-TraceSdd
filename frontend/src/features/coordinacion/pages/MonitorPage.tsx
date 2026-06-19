import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Users,
  AlertTriangle,
  CheckCircle2,
  MessageSquare,
  Clock,
  TrendingUp,
  Filter,
  X,
} from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useAuth } from '@/features/auth/context/AuthContext'
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

// ─── KPI Card ─────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string
  value: string | number
  icon: React.ElementType
  colorClass: string
  bgClass: string
  note?: string
}

function KpiCard({ label, value, icon: Icon, colorClass, bgClass, note }: KpiCardProps) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-surface-subtle bg-surface p-4 shadow-sm">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${bgClass}`}>
        <Icon className={`h-5 w-5 ${colorClass}`} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-text-muted">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-text leading-none">{value}</p>
        {note && <p className="mt-1 text-xs text-text-subtle">{note}</p>}
      </div>
    </div>
  )
}

// ─── Progress bar ─────────────────────────────────────────────────────────────

interface AlumnosBarProps {
  total: number
  al_dia: number
  atrasados: number
}

function AlumnosBar({ total, al_dia, atrasados }: AlumnosBarProps) {
  const pctAlDia = total > 0 ? Math.round((al_dia / total) * 100) : 0
  const pctAtrasados = total > 0 ? Math.round((atrasados / total) * 100) : 0

  return (
    <div className="rounded-xl border border-surface-subtle bg-surface p-5 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-text">Estado del grupo</h3>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-surface-subtle">
        <div
          className="h-full bg-emerald-500 transition-all duration-500"
          style={{ width: `${pctAlDia}%` }}
        />
        <div
          className="h-full bg-red-400 transition-all duration-500"
          style={{ width: `${pctAtrasados}%` }}
        />
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          Al día — {al_dia} ({pctAlDia}%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
          Atrasados — {atrasados} ({pctAtrasados}%)
        </span>
      </div>
    </div>
  )
}

// ─── MonitorContent ───────────────────────────────────────────────────────────

function MonitorContent() {
  const { asignacion, isLoadingAsignacion } = useAuth()
  const [filtros, setFiltros] = useState<MonitorFiltros | undefined>(undefined)
  const { data, isLoading, isError } = useMonitor(
    filtros,
    asignacion?.asignacionId,
    asignacion?.materiaId,
    !isLoadingAsignacion,
  )

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FiltroForm>({ resolver: zodResolver(filtroSchema) })

  const onSubmit = (formData: FiltroForm) => {
    setFiltros({
      desde: formData.desde || undefined,
      hasta: formData.hasta || undefined,
    })
  }

  const onLimpiar = () => {
    reset()
    setFiltros(undefined)
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-text">Monitor docente</h1>
        <p className="mt-0.5 text-sm text-text-muted">
          Métricas del cuatrimestre en tiempo real
        </p>
      </div>

      {/* Filtros */}
      <div className="rounded-xl border border-surface-subtle bg-surface p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <Filter className="h-4 w-4 text-text-muted" />
          <span className="text-sm font-medium text-text">Filtrar por período</span>
          {filtros && (
            <span className="ml-auto rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">
              Activo
            </span>
          )}
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted" htmlFor="desde">
              Desde
            </label>
            <input
              id="desde"
              type="date"
              {...register('desde')}
              className="rounded-lg border border-surface-subtle bg-surface-muted px-3 py-2 text-sm text-text focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted" htmlFor="hasta">
              Hasta
            </label>
            <input
              id="hasta"
              type="date"
              {...register('hasta')}
              className="rounded-lg border border-surface-subtle bg-surface-muted px-3 py-2 text-sm text-text focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            {errors.hasta && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {errors.hasta.message}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="submit"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              Aplicar
            </button>
            {filtros && (
              <button
                type="button"
                onClick={onLimpiar}
                className="flex items-center gap-1.5 rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text-muted hover:bg-surface-subtle hover:text-text"
              >
                <X className="h-3.5 w-3.5" />
                Limpiar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Métricas */}
      {isLoading ? (
        <div className="flex items-center gap-3 py-6">
          <Spinner />
          <span className="text-sm text-text-muted">Cargando métricas…</span>
        </div>
      ) : isError ? (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Error al cargar el monitor. Intentá de nuevo.
        </div>
      ) : data ? (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
            <KpiCard
              label="Total alumnos"
              value={data.total_alumnos}
              icon={Users}
              colorClass="text-brand-600"
              bgClass="bg-brand-50"
            />
            <KpiCard
              label="Atrasados"
              value={data.atrasados}
              icon={AlertTriangle}
              colorClass="text-red-500"
              bgClass="bg-red-50"
              note={data.atrasados > 0 ? 'Requieren atención' : undefined}
            />
            <KpiCard
              label="Al día"
              value={data.al_dia}
              icon={CheckCircle2}
              colorClass="text-emerald-600"
              bgClass="bg-emerald-50"
            />
            <KpiCard
              label="Comuns. enviadas"
              value={data.comunicaciones_enviadas}
              icon={MessageSquare}
              colorClass="text-purple-600"
              bgClass="bg-purple-50"
            />
            <KpiCard
              label="Pendientes"
              value={data.comunicaciones_pendientes}
              icon={Clock}
              colorClass="text-amber-500"
              bgClass="bg-amber-50"
              note={data.comunicaciones_pendientes > 0 ? 'Por aprobar' : undefined}
            />
            <KpiCard
              label="Promedio general"
              value={data.promedio_general != null ? data.promedio_general.toFixed(1) : '—'}
              icon={TrendingUp}
              colorClass="text-sky-600"
              bgClass="bg-sky-50"
            />
          </div>

          <AlumnosBar
            total={data.total_alumnos}
            al_dia={data.al_dia}
            atrasados={data.atrasados}
          />
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-surface-subtle bg-surface p-8 text-center">
          <Filter className="mx-auto mb-2 h-6 w-6 text-text-subtle" />
          <p className="text-sm text-text-muted">Aplicá un filtro para ver las métricas.</p>
        </div>
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
