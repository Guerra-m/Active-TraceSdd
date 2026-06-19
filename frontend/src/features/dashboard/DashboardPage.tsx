import { NavLink } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BookOpen,
  Calendar,
  CheckCircle2,
  DollarSign,
  Download,
  Inbox,
  MessageSquare,
  Users,
  UserCheck,
} from 'lucide-react'
import { useAuth } from '@/features/auth/context/AuthContext'
import { Spinner } from '@/shared/components/Spinner'
import { useMonitor } from '@/features/coordinacion/hooks/useMonitor'
import { useMisMensajes } from './hooks/useMisMensajes'
import { useMisCalificaciones } from './hooks/useMisCalificaciones'
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
  const { permissions, asignacion, isLoadingAsignacion } = useAuth()
  const canSeeMonitor = permissions.includes('atrasados:ver')

  const { data, isLoading, isError } = useMonitor(
    undefined,
    asignacion?.asignacionId,
    asignacion?.materiaId,
    canSeeMonitor && !isLoadingAsignacion,
  )

  if (!canSeeMonitor) return null

  if (isLoadingAsignacion || isLoading) {
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

// ─── Vista alumno ─────────────────────────────────────────────────────────────

function AlumnoDashboard() {
  const { data: cals, isLoading: loadingCals } = useMisCalificaciones()
  const { data: mensajes, isLoading: loadingMsgs } = useMisMensajes()

  // Agrupar calificaciones por materia
  const porMateria = (cals ?? []).reduce<Record<string, typeof cals>>((acc, c) => {
    const key = c.materia_nombre ?? 'Sin materia'
    ;(acc[key] = acc[key] ?? []).push(c)
    return acc
  }, {})

  const totalCals = cals?.length ?? 0
  const aprobadas = cals?.filter((c) => c.aprobado).length ?? 0
  const desaprobadas = totalCals - aprobadas
  const estaAlDia = totalCals > 0 && desaprobadas === 0

  return (
    <div className="space-y-6">
      {/* Estado general */}
      {!loadingCals && totalCals > 0 && (
        <div className={`flex items-center gap-3 rounded-xl border p-4 shadow-sm ${
          estaAlDia
            ? 'border-emerald-200 bg-emerald-50'
            : 'border-amber-200 bg-amber-50'
        }`}>
          {estaAlDia
            ? <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
            : <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />
          }
          <div>
            <p className={`text-sm font-semibold ${estaAlDia ? 'text-emerald-800' : 'text-amber-800'}`}>
              {estaAlDia ? 'Estás al día' : `Tenés ${desaprobadas} actividad${desaprobadas > 1 ? 'es' : ''} sin aprobar`}
            </p>
            <p className={`text-xs ${estaAlDia ? 'text-emerald-700' : 'text-amber-700'}`}>
              {aprobadas} de {totalCals} actividades aprobadas
            </p>
          </div>
        </div>
      )}

      {/* Calificaciones por materia */}
      {loadingCals ? (
        <div className="flex items-center gap-3 py-4">
          <Spinner />
          <span className="text-sm text-text-muted">Cargando calificaciones…</span>
        </div>
      ) : totalCals > 0 ? (
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-text">Mis calificaciones</h2>
          {Object.entries(porMateria).map(([materia, items]) => (
            <div key={materia} className="rounded-xl border border-surface-subtle bg-surface shadow-sm overflow-hidden">
              <div className="border-b border-surface-subtle bg-surface-muted px-4 py-2">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">{materia}</p>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-subtle">
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Actividad</th>
                    <th className="px-4 py-2 text-right font-medium text-text-muted">Nota</th>
                    <th className="px-4 py-2 text-center font-medium text-text-muted">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle">
                  {(items ?? []).map((c) => (
                    <tr key={c.actividad} className="hover:bg-surface-subtle">
                      <td className="px-4 py-2 text-text">{c.actividad}</td>
                      <td className="px-4 py-2 text-right font-mono text-text">
                        {c.nota_numerica != null
                          ? Number(c.nota_numerica).toFixed(1)
                          : c.nota_textual ?? <span className="text-text-subtle">—</span>}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {c.nota_numerica == null && !c.nota_textual ? (
                          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">Sin corregir</span>
                        ) : c.aprobado ? (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">Aprobado</span>
                        ) : (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">Desaprobado</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      ) : null}

      {/* Mensajes recibidos */}
      {loadingMsgs ? (
        <div className="flex items-center gap-3 py-4">
          <Spinner />
          <span className="text-sm text-text-muted">Cargando mensajes…</span>
        </div>
      ) : mensajes && mensajes.length > 0 ? (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Inbox className="h-4 w-4 text-text-muted" />
            <h2 className="text-sm font-semibold text-text">Mis mensajes</h2>
            <span className="ml-auto rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">
              {mensajes.length}
            </span>
          </div>
          <div className="space-y-2">
            {mensajes.map((m) => (
              <div key={m.id} className="rounded-xl border border-surface-subtle bg-surface p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-text">{m.asunto}</p>
                  <span className="shrink-0 text-[10px] text-text-subtle">
                    {new Date(m.created_at).toLocaleDateString('es-AR')}
                  </span>
                </div>
                <p className="mt-1 text-sm text-text-muted whitespace-pre-wrap">{m.cuerpo}</p>
              </div>
            ))}
          </div>
        </section>
      ) : !loadingCals && totalCals === 0 ? (
        <div className="rounded-xl border border-dashed border-surface-subtle bg-surface p-8 text-center">
          <p className="text-sm text-text-muted">No hay datos académicos disponibles aún.</p>
        </div>
      ) : null}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const { user, permissions } = useAuth()
  const isAlumno = user?.rol === 'ALUMNO'

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

      {isAlumno ? (
        <AlumnoDashboard />
      ) : (
        <>
          <KpiSection />
          <QuickAccess />
        </>
      )}
    </div>
  )
}
