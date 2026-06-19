import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { CheckCircle } from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { useClonarEquipo, useAsignacionMasiva } from '../hooks/useEquipos'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const paso1Schema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  cohorte_origen_id: z.string().min(1, 'La cohorte de origen es requerida'),
  cohorte_destino_id: z.string().min(1, 'La cohorte de destino es requerida'),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
  hasta: z.string().optional(),
})

const paso2Schema = z.object({
  usuario_ids_raw: z.string().min(1, 'Se requiere al menos un usuario'),
  rol: z.string().min(1, 'El rol es requerido'),
  materia_id: z.string().optional(),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
})

type Paso1Form = z.infer<typeof paso1Schema>
type Paso2Form = z.infer<typeof paso2Schema>

// ─── Shared styles ────────────────────────────────────────────────────────────

const inputCls = 'w-full rounded-lg border border-surface-subtle p-3 text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none bg-surface'
const labelCls = 'mb-1 block text-[11px] font-bold text-text-muted uppercase tracking-wider'
const errCls = 'mt-1 text-xs text-red-600'

// ─── Step indicator ───────────────────────────────────────────────────────────

function StepIndicator({ paso, totalPasos }: { paso: number; totalPasos: number }) {
  const stepLabels = ['Clonar equipo docente', 'Asignación masiva de usuarios']
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {Array.from({ length: totalPasos }, (_, i) => i + 1).map((n) => (
        <div key={n} className="flex items-center gap-2">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold flex-shrink-0 ${
                n < paso
                  ? 'bg-green-600 text-white'
                  : n === paso
                    ? 'bg-brand-600 text-white'
                    : 'bg-surface-subtle text-text-muted'
              }`}
            >
              {n < paso ? <CheckCircle className="w-5 h-5" /> : n}
            </div>
            <span className={`text-sm font-medium ${n === paso ? 'text-text' : 'text-text-muted'}`}>
              {stepLabels[n - 1]}
            </span>
          </div>
          {n < totalPasos && (
            <div className={`h-0.5 w-16 mx-1 ${n < paso ? 'bg-green-500' : 'bg-surface-subtle'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function SetupCuatrimestreContent() {
  const [paso, setPaso] = useState(1)
  const [, setNuevoEquipoId] = useState<string | null>(null)
  const [completado, setCompletado] = useState(false)

  const clonarMutation = useClonarEquipo()
  const asignacionMutation = useAsignacionMasiva()

  // Paso 1: Clonar equipo
  const {
    register: registerPaso1,
    handleSubmit: handlePaso1,
    formState: { errors: errorsPaso1 },
  } = useForm<Paso1Form>({ resolver: zodResolver(paso1Schema) })

  // Paso 2: Asignación masiva
  const {
    register: registerPaso2,
    handleSubmit: handlePaso2,
    formState: { errors: errorsPaso2 },
  } = useForm<Paso2Form>({ resolver: zodResolver(paso2Schema) })

  const onPaso1Submit = (data: Paso1Form) => {
    clonarMutation.mutate(
      {
        materia_id: data.materia_id,
        carrera_id: data.carrera_id,
        cohorte_origen_id: data.cohorte_origen_id,
        cohorte_destino_id: data.cohorte_destino_id,
        desde: data.desde,
        hasta: data.hasta || undefined,
      },
      {
        onSuccess: () => {
          setNuevoEquipoId('clonado')
          setPaso(2)
        },
      },
    )
  }

  const onPaso2Submit = (data: Paso2Form) => {
    const usuario_ids = data.usuario_ids_raw
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    asignacionMutation.mutate(
      {
        usuario_ids,
        rol: data.rol,
        materia_id: data.materia_id || undefined,
        desde: data.desde,
      },
      { onSuccess: () => setCompletado(true) },
    )
  }

  if (completado) {
    return (
      <div className="flex flex-col items-center gap-6 py-16">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-text">¡Setup completado!</h2>
        <p className="text-sm text-text-muted text-center max-w-sm">
          El equipo fue clonado y los usuarios fueron asignados exitosamente al nuevo cuatrimestre.
        </p>
        <button
          onClick={() => {
            setPaso(1)
            setNuevoEquipoId(null)
            setCompletado(false)
          }}
          className="rounded-lg bg-brand-600 px-6 py-2 text-sm text-white hover:bg-brand-700 transition-colors"
        >
          Nuevo setup
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div>
        <nav className="flex items-center gap-1 text-xs text-text-muted mb-1">
          <span>Coordinación</span>
          <span className="mx-0.5">›</span>
          <span className="text-text font-medium">Configuración de Institución</span>
        </nav>
        <h2 className="text-2xl font-bold tracking-tight text-text">Setup de Cuatrimestre</h2>
        <p className="text-sm text-text-muted mt-1">Configurá el equipo docente para el nuevo período académico.</p>
      </div>

      {/* Step Indicator */}
      <div className="p-5 bg-surface border border-surface-subtle rounded-xl shadow-sm">
        <StepIndicator paso={paso} totalPasos={2} />
      </div>

      {paso === 1 && (
        <div className="bg-surface rounded-xl border border-surface-subtle shadow-sm overflow-hidden">
          <div className="p-6 border-b border-surface-subtle bg-surface-muted">
            <h3 className="text-base font-semibold text-text">Paso 1: Clonar equipo docente</h3>
            <p className="text-sm text-text-muted mt-0.5">Copiá la estructura de equipo de un cuatrimestre anterior al nuevo.</p>
          </div>
          <div className="p-6">
            <form onSubmit={handlePaso1(onPaso1Submit)} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className={labelCls} htmlFor="materia_id">ID Materia</label>
                  <input id="materia_id" {...registerPaso1('materia_id')} className={`${inputCls} font-mono`} placeholder="UUID" />
                  {errorsPaso1.materia_id && <p role="alert" className={errCls}>{errorsPaso1.materia_id.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="carrera_id">ID Carrera</label>
                  <input id="carrera_id" {...registerPaso1('carrera_id')} className={`${inputCls} font-mono`} placeholder="UUID" />
                  {errorsPaso1.carrera_id && <p role="alert" className={errCls}>{errorsPaso1.carrera_id.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="cohorte_origen_id">Cohorte origen (ID)</label>
                  <input id="cohorte_origen_id" {...registerPaso1('cohorte_origen_id')} className={`${inputCls} font-mono`} placeholder="UUID" />
                  {errorsPaso1.cohorte_origen_id && <p role="alert" className={errCls}>{errorsPaso1.cohorte_origen_id.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="cohorte_destino_id">Cohorte destino (ID)</label>
                  <input id="cohorte_destino_id" {...registerPaso1('cohorte_destino_id')} className={`${inputCls} font-mono`} placeholder="UUID" />
                  {errorsPaso1.cohorte_destino_id && <p role="alert" className={errCls}>{errorsPaso1.cohorte_destino_id.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="p1-desde">Vigencia desde</label>
                  <input id="p1-desde" type="date" {...registerPaso1('desde')} className={inputCls} />
                  {errorsPaso1.desde && <p role="alert" className={errCls}>{errorsPaso1.desde.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="p1-hasta">Vigencia hasta (opcional)</label>
                  <input id="p1-hasta" type="date" {...registerPaso1('hasta')} className={inputCls} />
                </div>
              </div>
              {clonarMutation.isError && (
                <p role="alert" className={errCls}>
                  Error al clonar el equipo. Verificá los datos e intentá de nuevo.
                </p>
              )}
              <button
                type="submit"
                disabled={clonarMutation.isPending}
                className="rounded-lg bg-brand-600 px-6 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
              >
                {clonarMutation.isPending ? 'Clonando...' : 'Clonar y continuar →'}
              </button>
            </form>
          </div>
        </div>
      )}

      {paso === 2 && (
        <div className="bg-surface rounded-xl border border-surface-subtle shadow-sm overflow-hidden">
          <div className="p-6 border-b border-surface-subtle bg-surface-muted">
            <h3 className="text-base font-semibold text-text">Paso 2: Asignación masiva de usuarios</h3>
            <p className="text-sm text-green-700 mt-0.5 flex items-center gap-1">
              <CheckCircle className="w-4 h-4" />
              Equipo clonado exitosamente. Ahora asigná los usuarios al nuevo equipo.
            </p>
          </div>
          <div className="p-6">
            <form onSubmit={handlePaso2(onPaso2Submit)} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className={labelCls} htmlFor="rol">Rol a asignar</label>
                  <input id="rol" {...registerPaso2('rol')} className={inputCls} placeholder="TUTOR, PROFESOR..." />
                  {errorsPaso2.rol && <p role="alert" className={errCls}>{errorsPaso2.rol.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="p2-desde">Vigencia desde</label>
                  <input id="p2-desde" type="date" {...registerPaso2('desde')} className={inputCls} />
                  {errorsPaso2.desde && <p role="alert" className={errCls}>{errorsPaso2.desde.message}</p>}
                </div>
                <div>
                  <label className={labelCls} htmlFor="p2-materia">ID Materia (opcional)</label>
                  <input id="p2-materia" {...registerPaso2('materia_id')} className={`${inputCls} font-mono`} placeholder="UUID" />
                </div>
              </div>
              <div>
                <label className={labelCls} htmlFor="usuario_ids_raw">IDs de usuarios (uno por línea)</label>
                <textarea
                  id="usuario_ids_raw"
                  {...registerPaso2('usuario_ids_raw')}
                  rows={6}
                  placeholder={"uuid-1\nuuid-2\n..."}
                  className={`${inputCls} font-mono resize-none`}
                />
                {errorsPaso2.usuario_ids_raw && (
                  <p role="alert" className={errCls}>{errorsPaso2.usuario_ids_raw.message}</p>
                )}
              </div>
              {asignacionMutation.isError && (
                <p role="alert" className={errCls}>
                  Error en la asignación masiva. Intentá de nuevo.
                </p>
              )}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setPaso(1)}
                  className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors"
                >
                  ← Volver
                </button>
                <button
                  type="submit"
                  disabled={asignacionMutation.isPending}
                  className="rounded-lg bg-brand-600 px-6 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
                >
                  {asignacionMutation.isPending ? 'Asignando...' : 'Completar setup'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export function SetupCuatrimestrePage() {
  return (
    <RequirePermission permission="equipos:asignar">
      <SetupCuatrimestreContent />
    </RequirePermission>
  )
}
