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
  PenLine,
  Send,
  CheckCircle,
} from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useAuth } from '@/features/auth/context/AuthContext'
import { useMonitor } from '../hooks/useMonitor'
import { useCreateAviso } from '../hooks/useAvisos'
import type { MonitorFiltros, AvisoSeveridad } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

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

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  inicio_en: z.string().min(1, 'La fecha de inicio es requerida'),
  fin_en: z.string().optional(),
})

type AvisoForm = z.infer<typeof avisoSchema>

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
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 flex items-start gap-3 hover:border-on-primary-container transition-colors">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${bgClass}`}>
        <Icon className={`h-5 w-5 ${colorClass}`} />
      </div>
      <div className="min-w-0">
        <p className="text-label-caps font-label-caps text-on-surface-variant uppercase">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-on-surface leading-none">{value}</p>
        {note && <p className="mt-1 text-body-sm text-secondary">{note}</p>}
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
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
      <h3 className="mb-3 text-title-sm font-title-sm text-primary">Estado del grupo</h3>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-surface-container">
        <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${pctAlDia}%` }} />
        <div className="h-full bg-error transition-all duration-500" style={{ width: `${pctAtrasados}%` }} />
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-body-sm text-on-surface-variant">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          Al día — {al_dia} ({pctAlDia}%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-error" />
          Atrasados — {atrasados} ({pctAtrasados}%)
        </span>
      </div>
    </div>
  )
}

// ─── Severity option ──────────────────────────────────────────────────────────

const SEVERIDADES: { value: AvisoSeveridad; label: string; icon: React.ElementType; color: string }[] = [
  { value: 'Info', label: 'Información', icon: CheckCircle, color: 'text-secondary' },
  { value: 'Advertencia', label: 'Advertencia', icon: Clock, color: 'text-on-tertiary-fixed-variant' },
  { value: 'Crítico', label: 'Crítico', icon: AlertTriangle, color: 'text-error' },
]

// ─── MonitorContent ───────────────────────────────────────────────────────────

function MonitorContent() {
  const { asignacion, isLoadingAsignacion } = useAuth()
  const [filtros, setFiltros] = useState<MonitorFiltros | undefined>(undefined)
  const [severidad, setSeveridad] = useState<AvisoSeveridad>('Info')
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const { data, isLoading, isError } = useMonitor(
    filtros,
    asignacion?.asignacionId,
    asignacion?.materiaId,
    !isLoadingAsignacion,
  )

  const createAviso = useCreateAviso()

  // Filter form
  const {
    register: regFiltro,
    handleSubmit: handleFiltro,
    reset: resetFiltro,
    formState: { errors: filtroErrors },
  } = useForm<FiltroForm>({ resolver: zodResolver(filtroSchema) })

  const onFiltrar = (formData: FiltroForm) => {
    setFiltros({
      desde: formData.desde || undefined,
      hasta: formData.hasta || undefined,
    })
  }

  const onLimpiar = () => {
    resetFiltro()
    setFiltros(undefined)
  }

  // Aviso compose form
  const {
    register: regAviso,
    handleSubmit: handleAviso,
    reset: resetAviso,
    watch: watchAviso,
    formState: { errors: avisoErrors },
  } = useForm<AvisoForm>({
    resolver: zodResolver(avisoSchema),
    defaultValues: { inicio_en: new Date().toISOString().slice(0, 16) },
  })

  const tituloPreview = watchAviso('titulo') || 'Título del aviso'
  const cuerpoPreview = watchAviso('cuerpo') || 'El contenido del aviso aparecerá aquí…'

  const onPublicar = (formData: AvisoForm) => {
    createAviso.mutate(
      {
        titulo: formData.titulo,
        cuerpo: formData.cuerpo,
        severidad,
        alcance: 'Global',
        inicio_en: formData.inicio_en,
        fin_en: formData.fin_en || undefined,
        activo: true,
        requiere_ack: false,
      },
      {
        onSuccess: () => {
          resetAviso({ inicio_en: new Date().toISOString().slice(0, 16) })
          setSeveridad('Info')
          setSuccessMsg('Aviso publicado correctamente.')
          setTimeout(() => setSuccessMsg(null), 4000)
        },
      },
    )
  }

  const severidadStyles: Record<AvisoSeveridad, { bar: string; badge: string; label: string }> = {
    Crítico: { bar: 'bg-error', badge: 'bg-error-container text-on-error-container', label: 'URGENTE' },
    Advertencia: { bar: 'bg-tertiary', badge: 'bg-tertiary-fixed text-on-tertiary-fixed', label: 'IMPORTANTE' },
    Info: { bar: 'bg-secondary', badge: 'bg-surface-container-high text-on-surface-variant', label: 'INFO' },
  }
  const styles = severidadStyles[severidad]

  return (
    <div className="space-y-6 pb-8">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <nav className="flex items-center gap-1 text-body-sm text-on-surface-variant mb-1">
            <span>Coordinación</span>
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span className="font-bold text-primary">Monitor y Publicación de Avisos</span>
          </nav>
          <h1 className="text-display-lg font-display-lg text-primary">Monitor docente</h1>
        </div>
      </div>

      {/* Main grid: compose + preview */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: compose aviso form */}
        <section className="col-span-12 xl:col-span-7 space-y-6">
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <div className="flex items-center gap-2 mb-6 border-b border-outline-variant pb-4">
              <PenLine className="h-5 w-5 text-primary" />
              <h3 className="text-headline-md font-headline-md text-primary">Redactar aviso</h3>
            </div>

            <form onSubmit={handleAviso(onPublicar)} className="space-y-4">
              {/* Título */}
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="av-titulo">
                  TÍTULO
                </label>
                <input
                  id="av-titulo"
                  {...regAviso('titulo')}
                  className="w-full border border-outline-variant rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md"
                  placeholder="Ej: Recordatorio de entrega"
                />
                {avisoErrors.titulo && (
                  <p role="alert" className="text-sm text-error">{avisoErrors.titulo.message}</p>
                )}
              </div>

              {/* Cuerpo */}
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="av-cuerpo">
                  MENSAJE
                </label>
                <textarea
                  id="av-cuerpo"
                  {...regAviso('cuerpo')}
                  rows={4}
                  className="w-full border border-outline-variant rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md resize-none"
                  placeholder="Escribí el mensaje que verán los alumnos…"
                />
                {avisoErrors.cuerpo && (
                  <p role="alert" className="text-sm text-error">{avisoErrors.cuerpo.message}</p>
                )}
              </div>

              {/* Severidad */}
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase">
                  NIVEL DE SEVERIDAD
                </label>
                <div className="grid grid-cols-3 gap-4">
                  {SEVERIDADES.map((sev) => {
                    const Icon = sev.icon
                    const selected = severidad === sev.value
                    return (
                      <button
                        key={sev.value}
                        type="button"
                        onClick={() => setSeveridad(sev.value)}
                        className={`flex flex-col items-center justify-center p-4 border rounded-lg transition-all ${
                          selected
                            ? 'border-primary bg-primary-container text-on-primary-container ring-2 ring-primary'
                            : 'border-outline-variant hover:bg-surface-container cursor-pointer'
                        }`}
                      >
                        <Icon className={`h-5 w-5 mb-1 ${selected ? 'text-primary' : sev.color}`} />
                        <span className="text-label-caps font-label-caps">{sev.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Vigencia */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="av-inicio">
                    INICIO
                  </label>
                  <input
                    id="av-inicio"
                    type="datetime-local"
                    {...regAviso('inicio_en')}
                    className="w-full border border-outline-variant rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md"
                  />
                  {avisoErrors.inicio_en && (
                    <p role="alert" className="text-sm text-error">{avisoErrors.inicio_en.message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="av-fin">
                    FIN (OPCIONAL)
                  </label>
                  <input
                    id="av-fin"
                    type="datetime-local"
                    {...regAviso('fin_en')}
                    className="w-full border border-outline-variant rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md"
                  />
                </div>
              </div>

              {createAviso.isError && (
                <p role="alert" className="text-sm text-error">Error al publicar el aviso. Intentá de nuevo.</p>
              )}
              {successMsg && (
                <p className="text-sm text-emerald-700 font-medium">{successMsg}</p>
              )}

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={createAviso.isPending}
                  className="bg-primary text-on-primary px-6 py-2 rounded-lg text-title-sm flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                  {createAviso.isPending ? 'Publicando…' : 'Publicar Aviso'}
                </button>
              </div>
            </form>
          </div>

          {/* Monitor metrics filter */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4 border-b border-outline-variant pb-4">
              <Filter className="h-5 w-5 text-primary" />
              <h3 className="text-headline-md font-headline-md text-primary">Filtrar métricas por período</h3>
            </div>
            <form onSubmit={handleFiltro(onFiltrar)} className="flex flex-wrap items-end gap-4">
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="desde">
                  DESDE
                </label>
                <input
                  id="desde"
                  type="date"
                  {...regFiltro('desde')}
                  className="border border-outline-variant rounded-lg p-2 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md"
                />
              </div>
              <div className="space-y-1">
                <label className="block text-label-caps font-label-caps text-on-surface-variant uppercase" htmlFor="hasta">
                  HASTA
                </label>
                <input
                  id="hasta"
                  type="date"
                  {...regFiltro('hasta')}
                  className="border border-outline-variant rounded-lg p-2 focus:ring-2 focus:ring-primary focus:border-primary bg-surface transition-all text-body-md"
                />
                {filtroErrors.hasta && (
                  <p role="alert" className="text-sm text-error">{filtroErrors.hasta.message}</p>
                )}
              </div>
              <div className="flex items-center gap-2 pb-px">
                <button
                  type="submit"
                  className="bg-primary text-on-primary px-4 py-2 rounded-lg text-title-sm hover:opacity-90 transition-opacity"
                >
                  Aplicar
                </button>
                {filtros && (
                  <button
                    type="button"
                    onClick={onLimpiar}
                    className="flex items-center gap-1.5 border border-outline-variant px-3 py-2 rounded-lg text-body-sm text-on-surface-variant hover:bg-surface-container transition-colors"
                  >
                    <X className="h-3.5 w-3.5" />
                    Limpiar
                  </button>
                )}
                {filtros && (
                  <span className="rounded-full bg-secondary-container text-on-secondary-container px-3 py-0.5 text-label-caps font-label-caps">
                    Activo
                  </span>
                )}
              </div>
            </form>
          </div>

          {/* KPI Grid */}
          {isLoading ? (
            <div className="flex items-center gap-3 py-6">
              <Spinner />
              <span className="text-body-sm text-on-surface-variant">Cargando métricas…</span>
            </div>
          ) : isError ? (
            <div role="alert" className="rounded-xl border border-error-container bg-error-container/30 p-4 text-body-sm text-on-error-container">
              Error al cargar el monitor. Intentá de nuevo.
            </div>
          ) : data ? (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <KpiCard
                  label="Total alumnos"
                  value={data.total_alumnos}
                  icon={Users}
                  colorClass="text-secondary"
                  bgClass="bg-secondary-container"
                />
                <KpiCard
                  label="Atrasados"
                  value={data.atrasados}
                  icon={AlertTriangle}
                  colorClass="text-error"
                  bgClass="bg-error-container"
                  note={data.atrasados > 0 ? 'Requieren atención' : undefined}
                />
                <KpiCard
                  label="Al día"
                  value={data.al_dia}
                  icon={CheckCircle2}
                  colorClass="text-emerald-700"
                  bgClass="bg-emerald-50"
                />
                <KpiCard
                  label="Comunicaciones"
                  value={data.comunicaciones_enviadas}
                  icon={MessageSquare}
                  colorClass="text-secondary"
                  bgClass="bg-secondary-container"
                />
                <KpiCard
                  label="Pendientes"
                  value={data.comunicaciones_pendientes}
                  icon={Clock}
                  colorClass="text-on-tertiary-fixed-variant"
                  bgClass="bg-tertiary-fixed"
                  note={data.comunicaciones_pendientes > 0 ? 'Por aprobar' : undefined}
                />
                <KpiCard
                  label="Promedio general"
                  value={data.promedio_general != null ? data.promedio_general.toFixed(1) : '—'}
                  icon={TrendingUp}
                  colorClass="text-primary"
                  bgClass="bg-primary-fixed"
                />
              </div>

              <AlumnosBar
                total={data.total_alumnos}
                al_dia={data.al_dia}
                atrasados={data.atrasados}
              />
            </div>
          ) : (
            <div className="bg-surface-container-lowest border border-dashed border-outline-variant rounded-xl p-8 text-center">
              <Filter className="mx-auto mb-2 h-6 w-6 text-outline" />
              <p className="text-body-sm text-on-surface-variant">Aplicá un filtro para ver las métricas.</p>
            </div>
          )}
        </section>

        {/* Right: live preview */}
        <section className="col-span-12 xl:col-span-5">
          <div className="sticky top-24 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-label-caps font-label-caps text-on-surface-variant uppercase">Vista previa del aviso</h3>
              <div className="flex gap-1">
                <span className="w-3 h-3 rounded-full bg-error" />
                <span className="w-3 h-3 rounded-full bg-tertiary-fixed-dim" />
                <span className="w-3 h-3 rounded-full bg-secondary" />
              </div>
            </div>
            <div className="bg-surface-container-lowest border-2 border-primary rounded-xl overflow-hidden shadow-xl">
              <div className="bg-primary-container p-4 flex items-center justify-between text-on-primary">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  <span className="text-[10px] font-bold uppercase">Vista del alumno</span>
                </div>
              </div>
              <div className="p-6 bg-surface min-h-[300px] flex flex-col">
                <div className={`w-full h-1 mb-6 rounded-full ${styles.bar}`} />
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container shrink-0">
                    <AlertTriangle className="h-6 w-6" />
                  </div>
                  <div>
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase ${styles.badge}`}>
                      {styles.label}
                    </span>
                    <h4 className="text-headline-md font-headline-md text-primary mt-1 mb-1">
                      {tituloPreview}
                    </h4>
                    <p className="text-body-sm text-on-surface-variant">
                      Publicado por Coordinación · Ahora
                    </p>
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-body-md text-on-surface leading-relaxed whitespace-pre-wrap">
                    {cuerpoPreview}
                  </p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-secondary-container rounded-lg text-on-secondary-container flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
              <p className="text-body-sm">
                <strong>Consejo:</strong> Usá &ldquo;Crítico&rdquo; con moderación — el exceso de avisos urgentes genera fatiga en los alumnos.
              </p>
            </div>
          </div>
        </section>
      </div>
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
