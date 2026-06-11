import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useEquipos,
  useClonarEquipo,
  useModificarVigenciaBulk,
  useExportarEquipos,
} from '../hooks/useEquipos'
import type { AsignacionItem } from '../types'

// ─── Schemas Zod ─────────────────────────────────────────────────────────────

const clonarSchema = z.object({
  cohorte_destino_id: z.string().min(1, 'El ID de cohorte destino es requerido'),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
  hasta: z.string().optional(),
})

const vigenciaBulkSchema = z.object({
  desde: z.string().optional(),
  hasta: z.string().optional(),
}).refine((d) => d.desde || d.hasta, {
  message: 'Especificá al menos desde o hasta',
  path: ['desde'],
})

type ClonarForm = z.infer<typeof clonarSchema>
type VigenciaBulkForm = z.infer<typeof vigenciaBulkSchema>

// ─── Subcomponents ───────────────────────────────────────────────────────────

const ESTADO_BADGE: Record<string, string> = {
  vigente: 'bg-green-100 text-green-800',
  vencida: 'bg-red-100 text-red-800',
  futura: 'bg-blue-100 text-blue-800',
}

function AsignacionRow({
  item,
  onClonar,
  isSelected,
  onToggle,
}: {
  item: AsignacionItem
  onClonar: (item: AsignacionItem) => void
  isSelected: boolean
  onToggle: (id: string) => void
}) {
  return (
    <tr className="border-b border-border">
      <td className="p-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggle(item.id)}
          aria-label={`Seleccionar ${item.usuario_id}`}
        />
      </td>
      <td className="p-3 font-mono text-xs">{item.usuario_id}</td>
      <td className="p-3 font-medium">{item.rol}</td>
      <td className="p-3">{item.desde}</td>
      <td className="p-3">{item.hasta ?? '—'}</td>
      <td className="p-3">{item.comisiones.join(', ') || '—'}</td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${ESTADO_BADGE[item.estado_vigencia] ?? 'bg-gray-100 text-gray-700'}`}
        >
          {item.estado_vigencia}
        </span>
      </td>
      <td className="p-3">
        <button
          onClick={() => onClonar(item)}
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
        >
          Clonar
        </button>
      </td>
    </tr>
  )
}

// ─── Modal Clonar ─────────────────────────────────────────────────────────────

function ClonarModal({
  item,
  onClose,
}: {
  item: AsignacionItem
  onClose: () => void
}) {
  const clonarMutation = useClonarEquipo()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClonarForm>({ resolver: zodResolver(clonarSchema) })

  const onSubmit = (data: ClonarForm) => {
    if (!item.materia_id || !item.carrera_id || !item.cohorte_id) return
    clonarMutation.mutate(
      {
        materia_id: item.materia_id,
        carrera_id: item.carrera_id,
        cohorte_origen_id: item.cohorte_id,
        cohorte_destino_id: data.cohorte_destino_id,
        desde: data.desde,
        hasta: data.hasta ?? undefined,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-1 text-lg font-semibold">
          Clonar equipo: {item.rol}
        </h2>
        <p className="mb-4 text-xs text-gray-500">Cohorte origen: {item.cohorte_id ?? '—'}</p>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="cohorte_destino_id">
              ID Cohorte destino
            </label>
            <input
              id="cohorte_destino_id"
              {...register('cohorte_destino_id')}
              className="w-full rounded border border-border p-2"
              placeholder="UUID de la cohorte destino"
            />
            {errors.cohorte_destino_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.cohorte_destino_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="desde">
              Fecha inicio
            </label>
            <input
              id="desde"
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
            <label className="mb-1 block text-sm font-medium" htmlFor="hasta">
              Fecha fin (opcional)
            </label>
            <input
              id="hasta"
              type="date"
              {...register('hasta')}
              className="w-full rounded border border-border p-2"
            />
          </div>
          {clonarMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al clonar el equipo. Verificá los datos.
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
              disabled={clonarMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {clonarMutation.isPending ? 'Clonando...' : 'Clonar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Modal Vigencia Bulk ──────────────────────────────────────────────────────

function VigenciaBulkModal({
  items,
  onClose,
}: {
  items: AsignacionItem[]
  onClose: () => void
}) {
  const vigenciaMutation = useModificarVigenciaBulk()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VigenciaBulkForm>({ resolver: zodResolver(vigenciaBulkSchema) })

  const firstItem = items[0]

  const onSubmit = (data: VigenciaBulkForm) => {
    if (!firstItem?.materia_id || !firstItem?.carrera_id || !firstItem?.cohorte_id) return
    vigenciaMutation.mutate(
      {
        materia_id: firstItem.materia_id,
        carrera_id: firstItem.carrera_id,
        cohorte_id: firstItem.cohorte_id,
        desde: data.desde ?? undefined,
        hasta: data.hasta ?? undefined,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">
          Modificar vigencia ({items.length} asignaciones)
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="desde">
              Fecha inicio
            </label>
            <input
              id="desde"
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
            <label className="mb-1 block text-sm font-medium" htmlFor="hasta">
              Fecha fin
            </label>
            <input
              id="hasta"
              type="date"
              {...register('hasta')}
              className="w-full rounded border border-border p-2"
            />
          </div>
          {vigenciaMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al modificar vigencia. Intentá de nuevo.
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
              disabled={vigenciaMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {vigenciaMutation.isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

function EquiposContent() {
  const { data, isLoading, isError } = useEquipos()
  const exportMutation = useExportarEquipos()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [clonarTarget, setClonarTarget] = useState<AsignacionItem | null>(null)
  const [showVigenciaModal, setShowVigenciaModal] = useState(false)

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const handleExport = () => {
    exportMutation.mutate(undefined, {
      onSuccess: (blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'equipos.csv'
        a.click()
        URL.revokeObjectURL(url)
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded bg-red-50 p-4 text-red-700">
        Error al cargar los equipos. Intentá de nuevo.
      </div>
    )
  }

  const items = data ?? []
  const selectedItems = items.filter((i) => selectedIds.includes(i.id))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Equipos docentes</h1>
        <div className="flex gap-2">
          {selectedIds.length > 0 && (
            <button
              onClick={() => setShowVigenciaModal(true)}
              className="rounded border border-blue-600 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50"
            >
              Modificar vigencia ({selectedIds.length})
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="rounded border border-border px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Exportar
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-500">No hay asignaciones registradas.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left"></th>
                <th className="p-3 text-left">Usuario ID</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Desde</th>
                <th className="p-3 text-left">Hasta</th>
                <th className="p-3 text-left">Comisiones</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <AsignacionRow
                  key={item.id}
                  item={item}
                  onClonar={setClonarTarget}
                  isSelected={selectedIds.includes(item.id)}
                  onToggle={toggleSelect}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {clonarTarget && (
        <ClonarModal item={clonarTarget} onClose={() => setClonarTarget(null)} />
      )}

      {showVigenciaModal && (
        <VigenciaBulkModal
          items={selectedItems}
          onClose={() => {
            setShowVigenciaModal(false)
            setSelectedIds([])
          }}
        />
      )}
    </div>
  )
}

export function EquiposPage() {
  return (
    <RequirePermission permission="equipos:asignar">
      <EquiposContent />
    </RequirePermission>
  )
}
