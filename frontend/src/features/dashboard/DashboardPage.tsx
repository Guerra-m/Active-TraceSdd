import { NavLink } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BookOpen,
  Calendar,
  CheckCircle2,
  DollarSign,
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

      {isAlumno ? (
        /* Vista exclusiva alumno: calificaciones + mensajes */
        <AlumnoDashboard />
      ) : (
        <>
          {/* Métricas (roles con atrasados:ver) */}
          <KpiSection />
          {/* Accesos rápidos */}
          <QuickAccess />
        </>
      )}
    </div>
  )
}
