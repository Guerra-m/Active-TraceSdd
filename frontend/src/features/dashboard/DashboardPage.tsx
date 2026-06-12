import { NavLink } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BookOpen,
  Calendar,
  CheckCircle2,
  DollarSign,
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
  colorClass: string
  bgClass: string
  description?: string
}

function KpiCard({ label, value, icon: Icon, colorClass, bgClass, description }: KpiCardProps) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-surface-subtle bg-surface p-4 shadow-sm">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${bgClass}`}>
        <Icon className={`h-5 w-5 ${colorClass}`} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-text-muted">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-text leading-none">{value}</p>
        {description && <p className="mt-1 text-xs text-text-subtle">{description}</p>}
      </div>
    </div>
  )
}

// ─── Progress bar para al día vs atrasados ────────────────────────────────────

function AlumnosBar({ metrics }: { metrics: MonitorMetrics }) {
  const total = metrics.total_alumnos
  const pctAlDia = total > 0 ? Math.round((metrics.al_dia / total) * 100) : 0
  const pctAtrasados = 100 - pctAlDia

  return (
    <div className="rounded-xl border border-surface-subtle bg-surface p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-text mb-3">Estado de alumnos</h3>

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

      <div className="mt-3 flex items-center gap-6 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          Al día — {metrics.al_dia} ({pctAlDia}%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
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
    colorClass: 'text-blue-600',
    bgClass: 'bg-blue-50',
    permission: 'comunicacion:enviar',
  },
  {
    label: 'Monitor',
    description: 'Métricas del cuatrimestre',
    path: '/monitor',
    icon: BarChart3,
    colorClass: 'text-indigo-600',
    bgClass: 'bg-indigo-50',
    permission: 'atrasados:ver',
  },
  {
    label: 'Equipos docentes',
    description: 'Gestionar asignaciones de docentes',
    path: '/equipos',
    icon: Users,
    colorClass: 'text-teal-600',
    bgClass: 'bg-teal-50',
    permission: 'equipos:asignar',
  },
  {
    label: 'Encuentros',
    description: 'Administrar encuentros sincrónicos',
    path: '/encuentros/admin',
    icon: Calendar,
    colorClass: 'text-purple-600',
    bgClass: 'bg-purple-50',
    permission: 'encuentros:gestionar',
  },
  {
    label: 'Liquidaciones',
    description: 'Ver y gestionar liquidaciones',
    path: '/finanzas/liquidaciones',
    icon: DollarSign,
    colorClass: 'text-emerald-600',
    bgClass: 'bg-emerald-50',
    permission: 'liquidaciones:operar',
  },
  {
    label: 'Alumnos',
    description: 'Padrón de alumnos activos',
    path: '/alumnos',
    icon: UserCheck,
    colorClass: 'text-cyan-600',
    bgClass: 'bg-cyan-50',
    permission: 'padron:importar',
  },
  {
    label: 'Coloquios',
    description: 'Gestionar instancias de coloquio',
    path: '/coloquios',
    icon: BookOpen,
    colorClass: 'text-rose-600',
    bgClass: 'bg-rose-50',
    permission: 'coloquios:gestionar',
  },
]

function QuickAccess() {
  const { permissions } = useAuth()
  const visible = QUICK_LINKS.filter((l) => permissions.includes(l.permission))

  if (visible.length === 0) return null

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold text-text">Accesos rápidos</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {visible.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.path}
              to={link.path}
              className="group flex items-center gap-3 rounded-xl border border-surface-subtle bg-surface p-4 shadow-sm transition-shadow hover:shadow-md hover:border-brand-200"
            >
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${link.bgClass}`}
              >
                <Icon className={`h-4 w-4 ${link.colorClass}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text leading-tight">{link.label}</p>
                <p className="mt-0.5 text-xs text-text-muted leading-tight truncate">
                  {link.description}
                </p>
              </div>
              <ArrowRight className="h-3.5 w-3.5 shrink-0 text-text-subtle opacity-0 transition-opacity group-hover:opacity-100" />
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
        <span className="text-sm text-text-muted">Cargando métricas…</span>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-700">
        No se pudieron cargar las métricas del cuatrimestre.
      </div>
    )
  }

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
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
          icon={AlertTriangle}
          colorClass="text-amber-500"
          bgClass="bg-amber-50"
          description={data.comunicaciones_pendientes > 0 ? 'Requieren acción' : undefined}
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
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-text">
          {user ? `Hola, ${user.nombre.split(' ')[0]}` : 'Dashboard'}
        </h1>
        <p className="mt-0.5 text-sm text-text-muted">
          Resumen del cuatrimestre en curso
        </p>
      </div>

      {/* Métricas */}
      <KpiSection />

      {/* Accesos rápidos */}
      <QuickAccess />
    </div>
  )
}
