import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="materia_id">
                  ID Materia
                </label>
                <input
                  id="materia_id"
                  {...registerPaso1('materia_id')}
                  className="w-full rounded border border-border p-2"
                  placeholder="UUID"
                />
                {errorsPaso1.materia_id && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso1.materia_id.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="carrera_id">
                  ID Carrera
                </label>
                <input
                  id="carrera_id"
                  {...registerPaso1('carrera_id')}
                  className="w-full rounded border border-border p-2"
                  placeholder="UUID"
                />
                {errorsPaso1.carrera_id && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso1.carrera_id.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="cohorte_origen_id">
                  Cohorte origen (ID)
                </label>
                <input
                  id="cohorte_origen_id"
                  {...registerPaso1('cohorte_origen_id')}
                  className="w-full rounded border border-border p-2"
                  placeholder="UUID"
                />
                {errorsPaso1.cohorte_origen_id && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso1.cohorte_origen_id.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="cohorte_destino_id">
                  Cohorte destino (ID)
                </label>
                <input
                  id="cohorte_destino_id"
                  {...registerPaso1('cohorte_destino_id')}
                  className="w-full rounded border border-border p-2"
                  placeholder="UUID"
                />
                {errorsPaso1.cohorte_destino_id && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso1.cohorte_destino_id.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="p1-desde">
                  Vigencia desde
                </label>
                <input
                  id="p1-desde"
                  type="date"
                  {...registerPaso1('desde')}
                  className="w-full rounded border border-border p-2"
                />
                {errorsPaso1.desde && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso1.desde.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="p1-hasta">
                  Vigencia hasta (opcional)
                </label>
                <input
                  id="p1-hasta"
                  type="date"
                  {...registerPaso1('hasta')}
                  className="w-full rounded border border-border p-2"
                />
              </div>
            </div>
            {clonarMutation.isError && (
              <p role="alert" className="text-sm text-red-600">
                Error al clonar el equipo. Verificá los datos e intentá de nuevo.
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
          <h2 className="mb-4 text-lg font-semibold">Paso 2: Asignación masiva de usuarios</h2>
          <p className="mb-4 text-sm text-green-600">
            Equipo clonado exitosamente. Ahora asigná los usuarios al nuevo equipo.
          </p>
          <form onSubmit={handlePaso2(onPaso2Submit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="rol">
                  Rol a asignar
                </label>
                <input
                  id="rol"
                  {...registerPaso2('rol')}
                  className="w-full rounded border border-border p-2"
                  placeholder="TUTOR, PROFESOR..."
                />
                {errorsPaso2.rol && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso2.rol.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="p2-desde">
                  Vigencia desde
                </label>
                <input
                  id="p2-desde"
                  type="date"
                  {...registerPaso2('desde')}
                  className="w-full rounded border border-border p-2"
                />
                {errorsPaso2.desde && (
                  <p role="alert" className="mt-1 text-sm text-red-600">{errorsPaso2.desde.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="p2-materia">
                  ID Materia (opcional)
                </label>
                <input
                  id="p2-materia"
                  {...registerPaso2('materia_id')}
                  className="w-full rounded border border-border p-2"
                  placeholder="UUID"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="usuario_ids_raw">
                IDs de usuarios (uno por línea)
              </label>
              <textarea
                id="usuario_ids_raw"
                {...registerPaso2('usuario_ids_raw')}
                rows={6}
                placeholder="uuid-1&#10;uuid-2&#10;..."
                className="w-full rounded border border-border p-2 font-mono text-sm"
              />
              {errorsPaso2.usuario_ids_raw && (
                <p role="alert" className="mt-1 text-sm text-red-600">
                  {errorsPaso2.usuario_ids_raw.message}
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
