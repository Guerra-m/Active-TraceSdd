import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useFacturas, useCreateFactura, useAbonarFactura } from '../hooks/useFacturas'
import type { Factura, FacturaFiltros } from '../types'

// ─── Schemas Zod ──────────────────────────────────────────────────────────────

const filtrosSchema = z.object({
  docente_id: z.string().optional(),
  periodo: z.string().optional(),
  estado: z.enum(['pendiente', 'abonada', 'anulada']).optional(),
})

const facturaSchema = z.object({
  docente_id: z.string().min(1, 'El docente es requerido'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  periodo: z.string().min(7, 'Período requerido (YYYY-MM)'),
  numero_factura: z.string().min(1, 'El número de factura es requerido'),
  fecha_emision: z.string().min(1, 'La fecha de emisión es requerida'),
})

type FiltrosForm = z.infer<typeof filtrosSchema>
type FacturaForm = z.infer<typeof facturaSchema>

// ─── Modal Nueva Factura ──────────────────────────────────────────────────────

function NuevaFacturaModal({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateFactura()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FacturaForm>({ resolver: zodResolver(facturaSchema) })

  const onSubmit = (data: FacturaForm) => {
    createMutation.mutate(data, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Registrar nueva factura</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="f-docente">
              ID Docente
            </label>
            <input
              id="f-docente"
              {...register('docente_id')}
              className="w-full rounded border border-border p-2"
              placeholder="UUID del docente"
            />
            {errors.docente_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.docente_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="f-monto">
              Monto
            </label>
            <input
              id="f-monto"
              type="number"
              {...register('monto')}
              className="w-full rounded border border-border p-2"
            />
            {errors.monto && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.monto.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="f-periodo">
              Período (YYYY-MM)
            </label>
            <input
              id="f-periodo"
              {...register('periodo')}
              className="w-full rounded border border-border p-2"
              placeholder="2024-03"
            />
            {errors.periodo && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.periodo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="f-numero">
              Número de factura
            </label>
            <input
              id="f-numero"
              {...register('numero_factura')}
              className="w-full rounded border border-border p-2"
              placeholder="A-00001"
            />
            {errors.numero_factura && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.numero_factura.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="f-fecha">
              Fecha de emisión
            </label>
            <input
              id="f-fecha"
              type="date"
              {...register('fecha_emision')}
              className="w-full rounded border border-border p-2"
            />
            {errors.fecha_emision && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.fecha_emision.message}
              </p>
            )}
          </div>
          {createMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al registrar la factura. Intentá de nuevo.
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
              disabled={createMutation.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Fila Factura ─────────────────────────────────────────────────────────────

function FacturaRow({
  factura,
  onAbonar,
}: {
  factura: Factura
  onAbonar: (id: string) => void
}) {
  const fmt = (n: number) =>
    n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

  const estadoBadge: Record<Factura['estado'], string> = {
    pendiente: 'bg-yellow-100 text-yellow-800',
    abonada: 'bg-green-100 text-green-800',
    anulada: 'bg-red-100 text-red-800',
  }

  return (
    <tr className="border-b border-border">
      <td className="p-3">{factura.numero_factura}</td>
      <td className="p-3 font-medium">{factura.docente_nombre}</td>
      <td className="p-3">{factura.periodo}</td>
      <td className="p-3">{fmt(factura.monto)}</td>
      <td className="p-3">{factura.fecha_emision}</td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${estadoBadge[factura.estado]}`}
        >
          {factura.estado}
        </span>
      </td>
      <td className="p-3">
        {factura.estado === 'pendiente' && (
          <button
            onClick={() => onAbonar(factura.id)}
            className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700"
          >
            Marcar abonada
          </button>
        )}
      </td>
    </tr>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

function FacturasContent() {
  const [filtros, setFiltros] = useState<FacturaFiltros>({})
  const [showNueva, setShowNueva] = useState(false)

  const { data, isLoading, isError } = useFacturas(filtros)
  const abonarMutation = useAbonarFactura()

  const { register, handleSubmit } = useForm<FiltrosForm>({
    resolver: zodResolver(filtrosSchema),
  })

  const onFiltrar = (data: FiltrosForm) => {
    setFiltros({
      ...(data.docente_id ? { docente_id: data.docente_id } : {}),
      ...(data.periodo ? { periodo: data.periodo } : {}),
      ...(data.estado ? { estado: data.estado } : {}),
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
        Error al cargar las facturas. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Facturas</h1>
        <button
          onClick={() => setShowNueva(true)}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          + Nueva factura
        </button>
      </div>

      {/* Filtros */}
      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-border p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="fl-docente">
            Docente (ID)
          </label>
          <input
            id="fl-docente"
            {...register('docente_id')}
            className="rounded border border-border p-2 text-sm"
            placeholder="UUID"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="fl-periodo">
            Período
          </label>
          <input
            id="fl-periodo"
            {...register('periodo')}
            className="rounded border border-border p-2 text-sm"
            placeholder="2024-03"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="fl-estado">
            Estado
          </label>
          <select
            id="fl-estado"
            {...register('estado')}
            className="rounded border border-border p-2 text-sm"
          >
            <option value="">Todos</option>
            <option value="pendiente">Pendiente</option>
            <option value="abonada">Abonada</option>
            <option value="anulada">Anulada</option>
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            className="rounded border border-blue-600 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50"
          >
            Filtrar
          </button>
        </div>
      </form>

      {/* Tabla */}
      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay facturas para los filtros seleccionados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">N° Factura</th>
                <th className="p-3 text-left">Docente</th>
                <th className="p-3 text-left">Período</th>
                <th className="p-3 text-left">Monto</th>
                <th className="p-3 text-left">Fecha emisión</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((f) => (
                <FacturaRow
                  key={f.id}
                  factura={f}
                  onAbonar={(id) => abonarMutation.mutate(id)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {abonarMutation.isError && (
        <p role="alert" className="text-sm text-red-600">
          Error al marcar como abonada. Intentá de nuevo.
        </p>
      )}

      {showNueva && <NuevaFacturaModal onClose={() => setShowNueva(false)} />}
    </div>
  )
}

export function FacturasPage() {
  return (
    <RequirePermission permission="liquidaciones:ver">
      <FacturasContent />
    </RequirePermission>
  )
}
