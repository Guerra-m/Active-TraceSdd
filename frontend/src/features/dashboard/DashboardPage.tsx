import { NavLink } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BookOpen,
  Calendar,
  DollarSign,
  Download,
  MessageSquare,
  Users,
  UserCheck,
} from 'lucide-react'
import { useAuth } from '@/features/auth/context/AuthContext'
import { Spinner } from '@/shared/components/Spinner'
import { useMonitor } from '@/features/coordinacion/hooks/useMonitor'
import type { MonitorMetrics } from '@/features/coordinacion/types'

// ─── KPI Card ────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string
  value: number | string
  icon: React.ElementType
  iconBgClass: string
  iconColorClass: string
  badge?: string
  badgeClass?: string
  barColor?: string
  barPercent?: number
}

function KpiCard({
  label,
  value,
  icon: Icon,
  iconBgClass,
  iconColorClass,
  badge,
  badgeClass,
  barColor,
  barPercent,
}: KpiCardProps) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 hover:border-primary transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-2 rounded ${iconBgClass} ${iconColorClass}`}>
          <Icon className="h-5 w-5" />
        </div>
        {badge && (
          <span className={`font-mono text-xs font-bold ${badgeClass}`}>{badge}</span>
        )}
      </div>
      <h3 className="text-[11px] font-bold uppercase tracking-widest text-outline mb-1">
        {label}
      </h3>
      <div className="flex items-baseline gap-2">
        <span className="text-[30px] leading-[38px] tracking-tight font-semibold text-on-surface">
          {value}
        </span>
      </div>
      {barPercent !== undefined && barColor && (
        <div className="mt-4 h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${barColor}`}
            style={{ width: `${barPercent}%` }}
          />
        </div>
      )}
    </div>
  )
}

// ─── Progress bar para al día vs atrasados ────────────────────────────────────

function AlumnosBar({ metrics }: { metrics: MonitorMetrics }) {
  const total = metrics.total_alumnos
  const pctAlDia = total > 0 ? Math.round((metrics.al_dia / total) * 100) : 0
  const pctAtrasados = 100 - pctAlDia

  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6">
      <h3 className="text-[11px] font-bold uppercase tracking-widest text-outline mb-4">
        Estado de alumnos
      </h3>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-container">
        <div
          className="h-full bg-green-500 transition-all duration-500 rounded-l-full"
          style={{ width: `${pctAlDia}%` }}
        />
        <div
          className="h-full bg-error transition-all duration-500 rounded-r-full"
          style={{ width: `${pctAtrasados}%` }}
        />
      </div>
      <div className="mt-3 flex items-center gap-6 text-xs text-on-surface-variant">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
          Al día — {metrics.al_dia} ({pctAlDia}%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-error" />
          Atrasados — {metrics.atrasados} ({pctAtrasados}%)
        </span>
      </div>
    </div>
  )
}

// ─── Quick access card ────────────────────────────────────────────────────────

interface QuickLinkProps {
  label: string
  description: string
  path: string
  icon: React.ElementType
  colorClass: string
  bgClass: string
  permission: string
}

const QUICK_LINKS: QuickLinkProps[] = [
  {
    label: 'Atrasados',
    description: 'Ver alumnos con entregas pendientes',
    path: '/profesor/atrasados',
    icon: AlertTriangle,
    colorClass: 'text-amber-600',
    bgClass: 'bg-amber-50',
    permission: 'atrasados:ver',
  },
  {
    label: 'Comunicaciones',
    description: 'Enviar mensajes a alumnos',
    path: '/profesor/comunicaciones',
    icon: MessageSquare,
    colorClass: 'text-on-secondary-container',
    bgClass: 'bg-secondary-container',
    permission: 'comunicacion:enviar',
  },
  {
    label: 'Monitor',
    description: 'Métricas del cuatrimestre',
    path: '/monitor',
    icon: BarChart3,
    colorClass: 'text-on-primary-fixed',
    bgClass: 'bg-primary-fixed',
    permission: 'atrasados:ver',
  },
  {
    label: 'Equipos docentes',
    description: 'Gestionar asignaciones de docentes',
    path: '/equipos',
    icon: Users,
    colorClass: 'text-on-secondary-fixed',
    bgClass: 'bg-secondary-fixed-dim',
    permission: 'equipos:asignar',
  },
  {
    label: 'Encuentros',
    description: 'Administrar encuentros sincrónicos',
    path: '/encuentros/admin',
    icon: Calendar,
    colorClass: 'text-on-tertiary-fixed',
    bgClass: 'bg-tertiary-fixed',
    permission: 'encuentros:gestionar',
  },
  {
    label: 'Liquidaciones',
    description: 'Ver y gestionar liquidaciones',
    path: '/finanzas/liquidaciones',
    icon: DollarSign,
    colorClass: 'text-green-700',
    bgClass: 'bg-green-100',
    permission: 'liquidaciones:operar',
  },
  {
    label: 'Alumnos',
    description: 'Padrón de alumnos activos',
    path: '/alumnos',
    icon: UserCheck,
    colorClass: 'text-on-secondary-container',
    bgClass: 'bg-secondary-container',
    permission: 'padron:importar',
  },
  {
    label: 'Coloquios',
    description: 'Gestionar instancias de coloquio',
    path: '/coloquios',
    icon: BookOpen,
    colorClass: 'text-on-error-container',
    bgClass: 'bg-error-container',
    permission: 'coloquios:gestionar',
  },
]

function QuickAccess() {
  const { permissions } = useAuth()
  const visible = QUICK_LINKS.filter((l) => permissions.includes(l.permission))

  if (visible.length === 0) return null

  return (
    <section className="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-bright">
        <h3 className="text-[16px] leading-6 font-medium text-primary">Accesos rápidos</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 divide-x divide-y divide-outline-variant">
        {visible.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.path}
              to={link.path}
              className="group flex items-center gap-3 p-4 hover:bg-surface-container-low transition-colors"
            >
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded ${link.bgClass}`}
              >
                <Icon className={`h-4 w-4 ${link.colorClass}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[14px] font-medium text-on-surface leading-tight">
                  {link.label}
                </p>
                <p className="mt-0.5 text-[13px] text-on-surface-variant truncate">
                  {link.description}
                </p>
              </div>
              <ArrowRight className="h-3.5 w-3.5 shrink-0 text-outline opacity-0 transition-opacity group-hover:opacity-100" />
            </NavLink>
          )
        })}
      </div>
    </section>
  )
}

// ─── KPI Section ─────────────────────────────────────────────────────────────

function KpiSection() {
  const { data, isLoading, isError } = useMonitor()

  if (isLoading) {
    return (
      <div className="flex items-center gap-3 py-4">
        <Spinner />
        <span className="text-[14px] text-on-surface-variant">Cargando métricas…</span>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg bg-error-container border border-error/20 px-4 py-3 text-[14px] text-on-error-container">
        No se pudieron cargar las métricas del cuatrimestre.
      </div>
    )
  }

  const total = data.total_alumnos
  const pctAtRisk = total > 0 ? Math.round((data.atrasados / total) * 100) : 0
  const comTotal = data.comunicaciones_enviadas + data.comunicaciones_pendientes
  const pctPendingCom = comTotal > 0
    ? Math.round((data.comunicaciones_pendientes / comTotal) * 100)
    : 0

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KpiCard
          label="Alumnos en riesgo"
          value={data.atrasados}
          icon={AlertTriangle}
          iconBgClass="bg-error-container"
          iconColorClass="text-on-error-container"
          badge={`+${pctAtRisk}% del total`}
          badgeClass="text-error"
          barColor="bg-error"
          barPercent={pctAtRisk}
        />
        <KpiCard
          label="Total alumnos"
          value={data.total_alumnos}
          icon={Users}
          iconBgClass="bg-tertiary-fixed"
          iconColorClass="text-on-tertiary-fixed"
          badge={`${data.al_dia} al día`}
          badgeClass="text-tertiary-container"
          barColor="bg-tertiary-container"
          barPercent={total > 0 ? Math.round((data.al_dia / total) * 100) : 0}
        />
        <KpiCard
          label="Comunicaciones pendientes"
          value={data.comunicaciones_pendientes}
          icon={MessageSquare}
          iconBgClass="bg-secondary-container"
          iconColorClass="text-on-secondary-container"
          badge={`${data.comunicaciones_enviadas} enviadas`}
          badgeClass="text-secondary"
          barColor="bg-primary"
          barPercent={pctPendingCom}
        />
      </div>
      <AlumnosBar metrics={data} />
    </section>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-[13px] text-outline mb-1">
            <span>Dashboard</span>
            <ArrowRight className="h-3 w-3" />
            <span className="text-on-surface-variant">Resumen académico</span>
          </nav>
          <h2 className="text-[30px] leading-[38px] tracking-tight font-semibold text-on-background">
            {user ? `Hola, ${user.nombre.split(' ')[0]}` : 'Dashboard'}
          </h2>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-1.5 px-4 py-2 bg-surface-container-lowest border border-outline-variant rounded text-[14px] hover:bg-surface-container transition-colors">
            <Calendar className="h-4 w-4" />
            Cuatrimestre actual
          </button>
          <button className="flex items-center gap-1.5 px-4 py-2 bg-primary text-on-primary rounded text-[14px] hover:opacity-90 transition-colors">
            <Download className="h-4 w-4" />
            Exportar reporte
          </button>
        </div>
      </div>

      {/* Métricas KPI */}
      <KpiSection />

      {/* Accesos rápidos */}
      <QuickAccess />
    </div>
  )
}
