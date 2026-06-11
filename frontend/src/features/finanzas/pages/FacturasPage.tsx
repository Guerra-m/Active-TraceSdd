import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useFacturas, useCreateFactura, useAbonarFactura } from '../hooks/useFacturas'
import type { Factura, FacturaEstado, FacturaFiltros } from '../types'

// ─── Schemas Zod ──────────────────────────────────────────────────────────────

const filtrosSchema = z.object({
  usuario_id: z.string().optional(),
  periodo: z.string().optional(),
  estado: z.enum(['Pendiente', 'Abonada']).optional(),
})

const facturaSchema = z.object({
  usuario_id: z.string().min(1, 'El usuario es requerido'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  periodo: z.string().min(7, 'Período requerido (YYYY-MM)'),
  detalle: z.string().optional(),
  archivo_ref: z.string().optional(),
})

const abonarSchema = z.object({
  fecha_pago: z.string().min(1, 'La fecha de pago es requerida'),
})

type FiltrosForm = z.infer<typeof filtrosSchema>
type FacturaForm = z.infer<typeof facturaSchema>
type AbonarForm = z.infer<typeof abonarSchema>

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
            <label className="mb-1 block text-sm font-medium" htmlFor="f-usuario">
              ID Usuario
            </label>
            <input
              id="f-usuario"
              {...register('usuario_id')}
              className="w-full rounded border border-border p-2"
              placeholder="UUID del usuario"
            />
            {errors.usuario_id && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.usuario_id.message}
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
            <label className="mb-1 block text-sm font-medium" htmlFor="f-detalle">
              Detalle (opcional)
            </label>
            <input
              id="f-detalle"
              {...register('detalle')}
              className="w-full rounded border border-border p-2"
            />
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

// ─── Modal Abonar ─────────────────────────────────────────────────────────────

function AbonarModal({
  facturaId,
  onClose,
}: {
  facturaId: string
  onClose: () => void
}) {
  const abonarMutation = useAbonarFactura()
  const { register, handleSubmit, formState: { errors } } = useForm<AbonarForm>({
    resolver: zodResolver(abonarSchema),
    defaultValues: { fecha_pago: new Date().toISOString().slice(0, 10) },
  })

  const onSubmit = (data: AbonarForm) => {
    abonarMutation.mutate({ id: facturaId, fecha_pago: data.fecha_pago }, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Marcar como abonada</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="ab-fecha">
              Fecha de pago
            </label>
            <input
              id="ab-fecha"
              type="date"
              {...register('fecha_pago')}
              className="w-full rounded border border-border p-2"
            />
            {errors.fecha_pago && (
              <p role="alert" className="mt-1 text-sm text-red-600">
                {errors.fecha_pago.message}
              </p>
            )}
          </div>
          {abonarMutation.isError && (
            <p role="alert" className="text-sm text-red-600">
              Error al abonar la factura. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border border-border px-4 py-2 text-sm">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={abonarMutation.isPending}
              className="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            >
              {abonarMutation.isPending ? 'Guardando...' : 'Confirmar'}
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

  const estadoBadge: Record<FacturaEstado, string> = {
    Pendiente: 'bg-yellow-100 text-yellow-800',
    Abonada: 'bg-green-100 text-green-800',
  }

  return (
    <tr className="border-b border-border">
      <td className="p-3 font-mono text-xs text-gray-500">{factura.usuario_id.slice(0, 8)}</td>
      <td className="p-3">{factura.periodo}</td>
      <td className="p-3">{fmt(factura.monto)}</td>
      <td className="p-3 text-gray-500 text-xs">{factura.detalle ?? '—'}</td>
      <td className="p-3">{factura.fecha_carga.slice(0, 10)}</td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${estadoBadge[factura.estado]}`}
        >
          {factura.estado}
        </span>
      </td>
      <td className="p-3">
        {factura.estado === 'Pendiente' && (
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
  const [abonarId, setAbonarId] = useState<string | null>(null)

  const { data, isLoading, isError } = useFacturas(filtros)
  const items = data ?? []

  const { register, handleSubmit } = useForm<FiltrosForm>({
    resolver: zodResolver(filtrosSchema),
  })

  const onFiltrar = (formData: FiltrosForm) => {
    setFiltros({
      ...(formData.usuario_id ? { usuario_id: formData.usuario_id } : {}),
      ...(formData.periodo ? { periodo: formData.periodo } : {}),
      ...(formData.estado ? { estado: formData.estado } : {}),
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

      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-border p-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500" htmlFor="fl-usuario">
            Usuario (ID)
          </label>
          <input
            id="fl-usuario"
            {...register('usuario_id')}
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
            <option value="Pendiente">Pendiente</option>
            <option value="Abonada">Abonada</option>
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

      {items.length === 0 ? (
        <p className="text-gray-500">No hay facturas para los filtros seleccionados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Usuario (ID)</th>
                <th className="p-3 text-left">Período</th>
                <th className="p-3 text-left">Monto</th>
                <th className="p-3 text-left">Detalle</th>
                <th className="p-3 text-left">Fecha carga</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((f) => (
                <FacturaRow
                  key={f.id}
                  factura={f}
                  onAbonar={(id) => setAbonarId(id)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showNueva && <NuevaFacturaModal onClose={() => setShowNueva(false)} />}
      {abonarId && <AbonarModal facturaId={abonarId} onClose={() => setAbonarId(null)} />}
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
