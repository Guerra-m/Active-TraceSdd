import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useSalariosBase,
  useCreateSalarioBase,
  useUpdateSalarioBase,
  useSalariosPlus,
  useCreateSalarioPlus,
  useUpdateSalarioPlus,
} from '../hooks/useSalarios'
import type { SalarioBase, SalarioPlus } from '../types'

// ─── Schemas Zod ──────────────────────────────────────────────────────────────

const salarioSchema = z.object({
  rol: z.string().min(1, 'El rol es requerido'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  desde: z.string().min(1, 'La fecha desde es requerida'),
  hasta: z.string().optional(),
})

type SalarioForm = z.infer<typeof salarioSchema>

// ─── Modal Salario ────────────────────────────────────────────────────────────

function SalarioModal({
  tipo,
  salario,
  onClose,
}: {
  tipo: 'base' | 'plus'
  salario?: SalarioBase | SalarioPlus
  onClose: () => void
}) {
  const createBase = useCreateSalarioBase()
  const updateBase = useUpdateSalarioBase()
  const createPlus = useCreateSalarioPlus()
  const updatePlus = useUpdateSalarioPlus()

  const isEditing = Boolean(salario)
  const isPending =
    tipo === 'base'
      ? isEditing
        ? updateBase.isPending
        : createBase.isPending
      : isEditing
        ? updatePlus.isPending
        : createPlus.isPending

  const isError =
    tipo === 'base'
      ? isEditing
        ? updateBase.isError
        : createBase.isError
      : isEditing
        ? updatePlus.isError
        : createPlus.isError

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioForm>({
    resolver: zodResolver(salarioSchema),
    defaultValues: salario
      ? {
          rol: salario.rol,
          monto: salario.monto,
          desde: salario.desde,
          hasta: salario.hasta ?? undefined,
        }
      : {},
  })

  const onSubmit = (data: SalarioForm) => {
    if (tipo === 'base') {
      if (isEditing && salario) {
        updateBase.mutate(
          { id: salario.id, payload: data },
          { onSuccess: onClose },
        )
      } else {
        createBase.mutate(data, { onSuccess: onClose })
      }
    } else {
      if (isEditing && salario) {
        updatePlus.mutate(
          { id: salario.id, payload: data },
          { onSuccess: onClose },
        )
      } else {
        createPlus.mutate(data, { onSuccess: onClose })
      }
    }
  }

  const titulo = `${isEditing ? 'Editar' : 'Nuevo'} salario ${tipo === 'base' ? 'base' : 'plus'}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{titulo}</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="s-rol">
              Rol
            </label>
            <input
              id="s-rol"
              {...register('rol')}
              className="w-full rounded border border-border p-2"
              placeholder="Ej: TUTOR"
            />
            {errors.rol && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.rol.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="s-monto">
              Monto
            </label>
            <input
              id="s-monto"
              type="number"
              {...register('monto')}
              className="w-full rounded border border-border p-2"
              placeholder="80000"
            />
            {errors.monto && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.monto.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="s-desde">
              Desde
            </label>
            <input
              id="s-desde"
              type="date"
              {...register('desde')}
              className="w-full rounded border border-border p-2"
            />
            {errors.desde && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.desde.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="s-hasta">
              Hasta (opcional)
            </label>
            <input
              id="s-hasta"
              type="date"
              {...register('hasta')}
              className="w-full rounded border border-border p-2"
            />
          </div>
          {isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al guardar el salario. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-border px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Tabla Salarios ───────────────────────────────────────────────────────────

function SalariosTable({
  titulo,
  tipo,
  items,
  onNuevo,
  onEditar,
}: {
  titulo: string
  tipo: 'base' | 'plus'
  items: (SalarioBase | SalarioPlus)[]
  onNuevo: () => void
  onEditar: (s: SalarioBase | SalarioPlus) => void
}) {
  const fmt = (n: number) =>
    n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border bg-gray-50 px-4 py-3">
        <h2 className="font-semibold">{titulo}</h2>
        <button
          onClick={onNuevo}
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
        >
          + Nuevo
        </button>
      </div>
      {items.length === 0 ? (
        <p className="p-4 text-gray-500">No hay registros de salario {tipo}.</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3 text-left">Rol</th>
              <th className="p-3 text-left">Monto</th>
              <th className="p-3 text-left">Desde</th>
              <th className="p-3 text-left">Hasta</th>
              <th className="p-3 text-left">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id} className="border-b border-border">
                <td className="p-3 font-medium">{s.rol}</td>
                <td className="p-3">{fmt(s.monto)}</td>
                <td className="p-3">{s.desde}</td>
                <td className="p-3">{s.hasta ?? '—'}</td>
                <td className="p-3">
                  <button
                    onClick={() => onEditar(s)}
                    className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

type ModalState =
  | null
  | { tipo: 'base'; salario?: SalarioBase }
  | { tipo: 'plus'; salario?: SalarioPlus }

function GrillaSalarialContent() {
  const [modal, setModal] = useState<ModalState>(null)

  const { data: salariosBase, isLoading: loadingBase } = useSalariosBase()
  const { data: salariosPlus, isLoading: loadingPlus } = useSalariosPlus()

  if (loadingBase || loadingPlus) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Grilla salarial</h1>

      <SalariosTable
        titulo="Salario Base"
        tipo="base"
        items={salariosBase ?? []}
        onNuevo={() => setModal({ tipo: 'base' })}
        onEditar={(s) => setModal({ tipo: 'base', salario: s as SalarioBase })}
      />

      <SalariosTable
        titulo="Salario Plus"
        tipo="plus"
        items={salariosPlus ?? []}
        onNuevo={() => setModal({ tipo: 'plus' })}
        onEditar={(s) => setModal({ tipo: 'plus', salario: s as SalarioPlus })}
      />

      {modal && (
        <SalarioModal
          tipo={modal.tipo}
          salario={modal.tipo === 'base' ? modal.salario : modal.salario}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}

export function GrillaSalarialPage() {
  return (
    <RequirePermission permission="liquidaciones:gestionar">
      <GrillaSalarialContent />
    </RequirePermission>
  )
}
