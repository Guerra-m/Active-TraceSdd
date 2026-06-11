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
import type { Equipo } from '../types'

// ─── Schemas Zod ─────────────────────────────────────────────────────────────

const clonarSchema = z.object({
  periodo_destino: z.string().min(1, 'El período destino es requerido'),
})

const vigenciaBulkSchema = z.object({
  fecha_inicio: z.string().min(1, 'Fecha inicio requerida'),
  fecha_fin: z.string().min(1, 'Fecha fin requerida'),
})

type ClonarForm = z.infer<typeof clonarSchema>
type VigenciaBulkForm = z.infer<typeof vigenciaBulkSchema>

// ─── Subcomponents ───────────────────────────────────────────────────────────

function EquipoRow({
  equipo,
  onClonar,
  isSelected,
  onToggle,
}: {
  equipo: Equipo
  onClonar: (equipo: Equipo) => void
  isSelected: boolean
  onToggle: (id: string) => void
}) {
  return (
    <tr className="border-b border-border">
      <td className="p-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggle(equipo.id)}
          aria-label={`Seleccionar ${equipo.nombre}`}
        />
      </td>
      <td className="p-3 font-medium">{equipo.nombre}</td>
      <td className="p-3">{equipo.periodo}</td>
      <td className="p-3">{equipo.fecha_inicio}</td>
      <td className="p-3">{equipo.fecha_fin}</td>
      <td className="p-3">{equipo.tutores_count}</td>
      <td className="p-3">
        <button
          onClick={() => onClonar(equipo)}
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
  equipo,
  onClose,
}: {
  equipo: Equipo
  onClose: () => void
}) {
  const clonarMutation = useClonarEquipo()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClonarForm>({ resolver: zodResolver(clonarSchema) })

  const onSubmit = (data: ClonarForm) => {
    clonarMutation.mutate(
      { equipoId: equipo.id, payload: data },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Clonar equipo: {equipo.nombre}</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="periodo_destino">
              Período destino
            </label>
            <input
              id="periodo_destino"
              {...register('periodo_destino')}
              className="w-full rounded border border-border p-2"
              placeholder="Ej: 2024-2"
            />
            {errors.periodo_destino && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.periodo_destino.message}
              </p>
            )}
          </div>
          {clonarMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al clonar el equipo. Intentá de nuevo.
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
  equipoIds,
  onClose,
}: {
  equipoIds: string[]
  onClose: () => void
}) {
  const vigenciaMutation = useModificarVigenciaBulk()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VigenciaBulkForm>({ resolver: zodResolver(vigenciaBulkSchema) })

  const onSubmit = (data: VigenciaBulkForm) => {
    vigenciaMutation.mutate(
      { equipo_ids: equipoIds, ...data },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Modificar vigencia ({equipoIds.length} equipos)</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="fecha_inicio">
              Fecha inicio
            </label>
            <input
              id="fecha_inicio"
              type="date"
              {...register('fecha_inicio')}
              className="w-full rounded border border-border p-2"
            />
            {errors.fecha_inicio && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.fecha_inicio.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="fecha_fin">
              Fecha fin
            </label>
            <input
              id="fecha_fin"
              type="date"
              {...register('fecha_fin')}
              className="w-full rounded border border-border p-2"
            />
            {errors.fecha_fin && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.fecha_fin.message}
              </p>
            )}
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
  const [clonarTarget, setClonarTarget] = useState<Equipo | null>(null)
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

      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay equipos registrados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left"></th>
                <th className="p-3 text-left">Nombre</th>
                <th className="p-3 text-left">Período</th>
                <th className="p-3 text-left">Inicio</th>
                <th className="p-3 text-left">Fin</th>
                <th className="p-3 text-left">Tutores</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((equipo) => (
                <EquipoRow
                  key={equipo.id}
                  equipo={equipo}
                  onClonar={setClonarTarget}
                  isSelected={selectedIds.includes(equipo.id)}
                  onToggle={toggleSelect}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {clonarTarget && (
        <ClonarModal equipo={clonarTarget} onClose={() => setClonarTarget(null)} />
      )}

      {showVigenciaModal && (
        <VigenciaBulkModal
          equipoIds={selectedIds}
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
