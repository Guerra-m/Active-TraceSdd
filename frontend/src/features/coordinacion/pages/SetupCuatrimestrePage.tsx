import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { useClonarEquipo, useAsignacionMasiva } from '../hooks/useEquipos'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const paso1Schema = z.object({
  equipo_id: z.string().min(1, 'El ID del equipo es requerido'),
  periodo_destino: z.string().min(1, 'El período destino es requerido'),
})

const paso2Schema = z.object({
  tutor_id: z.string().min(1, 'El tutor es requerido'),
  alumno_ids_raw: z.string().min(1, 'Se requiere al menos un alumno'),
})

type Paso1Form = z.infer<typeof paso1Schema>
type Paso2Form = z.infer<typeof paso2Schema>

// ─── Step indicator ───────────────────────────────────────────────────────────

function StepIndicator({ paso, totalPasos }: { paso: number; totalPasos: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: totalPasos }, (_, i) => i + 1).map((n) => (
        <div key={n} className="flex items-center gap-2">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
              n < paso
                ? 'bg-green-600 text-white'
                : n === paso
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
            }`}
          >
            {n < paso ? '✓' : n}
          </div>
          {n < totalPasos && <div className={`h-0.5 w-12 ${n < paso ? 'bg-green-600' : 'bg-gray-200'}`} />}
        </div>
      ))}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function SetupCuatrimestreContent() {
  const [paso, setPaso] = useState(1)
  const [nuevoEquipoId, setNuevoEquipoId] = useState<string | null>(null)
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
      { equipoId: data.equipo_id, payload: { periodo_destino: data.periodo_destino } },
      {
        onSuccess: (nuevoEquipo) => {
          setNuevoEquipoId(nuevoEquipo.id)
          setPaso(2)
        },
      },
    )
  }

  const onPaso2Submit = (data: Paso2Form) => {
    if (!nuevoEquipoId) return
    const alumno_ids = data.alumno_ids_raw
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    asignacionMutation.mutate(
      { equipoId: nuevoEquipoId, payload: { tutor_id: data.tutor_id, alumno_ids } },
      { onSuccess: () => setCompletado(true) },
    )
  }

  if (completado) {
    return (
      <div className="flex flex-col items-center gap-4 py-12">
        <div className="text-5xl">✅</div>
        <h2 className="text-xl font-semibold text-green-700">¡Setup completado!</h2>
        <p className="text-gray-500">
          El equipo fue clonado y los alumnos fueron asignados exitosamente.
        </p>
        <button
          onClick={() => {
            setPaso(1)
            setNuevoEquipoId(null)
            setCompletado(false)
          }}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Nuevo setup
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Setup de cuatrimestre</h1>
      <StepIndicator paso={paso} totalPasos={2} />

      {paso === 1 && (
        <div className="rounded-lg border border-border p-6">
          <h2 className="mb-4 text-lg font-semibold">Paso 1: Clonar equipo docente</h2>
          <form onSubmit={handlePaso1(onPaso1Submit)} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="equipo_id">
                ID del equipo a clonar
              </label>
              <input
                id="equipo_id"
                {...registerPaso1('equipo_id')}
                className="w-full rounded border border-border p-2"
                placeholder="UUID del equipo"
              />
              {errorsPaso1.equipo_id && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errorsPaso1.equipo_id.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="periodo_destino">
                Período destino
              </label>
              <input
                id="periodo_destino"
                {...registerPaso1('periodo_destino')}
                className="w-full rounded border border-border p-2"
                placeholder="Ej: 2024-2"
              />
              {errorsPaso1.periodo_destino && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errorsPaso1.periodo_destino.message}
                </p>
              )}
            </div>
            {clonarMutation.isError && (
              <p role="alert" className="text-sm text-red-600">
                Error al clonar el equipo. Verificá el ID e intentá de nuevo.
              </p>
            )}
            <button
              type="submit"
              disabled={clonarMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {clonarMutation.isPending ? 'Clonando...' : 'Clonar y continuar'}
            </button>
          </form>
        </div>
      )}

      {paso === 2 && (
        <div className="rounded-lg border border-border p-6">
          <h2 className="mb-4 text-lg font-semibold">Paso 2: Asignación masiva de alumnos</h2>
          <p className="mb-4 text-sm text-green-600">
            Equipo clonado exitosamente. ID del nuevo equipo: {nuevoEquipoId}
          </p>
          <form onSubmit={handlePaso2(onPaso2Submit)} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="tutor_id">
                ID del tutor
              </label>
              <input
                id="tutor_id"
                {...registerPaso2('tutor_id')}
                className="w-full rounded border border-border p-2"
                placeholder="UUID del tutor"
              />
              {errorsPaso2.tutor_id && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errorsPaso2.tutor_id.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="alumno_ids_raw">
                IDs de alumnos (uno por línea)
              </label>
              <textarea
                id="alumno_ids_raw"
                {...registerPaso2('alumno_ids_raw')}
                rows={6}
                placeholder="alumno-uuid-1&#10;alumno-uuid-2&#10;..."
                className="w-full rounded border border-border p-2 font-mono text-sm"
              />
              {errorsPaso2.alumno_ids_raw && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errorsPaso2.alumno_ids_raw.message}
                </p>
              )}
            </div>
            {asignacionMutation.isError && (
              <p role="alert" className="text-sm text-red-600">
                Error en la asignación masiva. Intentá de nuevo.
              </p>
            )}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPaso(1)}
                className="rounded border border-border px-4 py-2 text-sm hover:bg-gray-50"
              >
                Volver
              </button>
              <button
                type="submit"
                disabled={asignacionMutation.isPending}
                className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {asignacionMutation.isPending ? 'Asignando...' : 'Completar setup'}
              </button>
            </div>
          </form>
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
