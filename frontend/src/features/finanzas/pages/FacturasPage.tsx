import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ReceiptText,
  FileDown,
  Filter,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Building2,
  Download,
  MoreVertical,
  ChevronRight,
} from 'lucide-react'
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

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

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
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl border border-[#c4c6cd]">
        <h2 className="mb-4 text-lg font-semibold text-primary">Registrar nueva factura</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="f-usuario">
              ID Usuario
            </label>
            <input
              id="f-usuario"
              {...register('usuario_id')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="UUID del usuario"
            />
            {errors.usuario_id && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.usuario_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="f-monto">
              Monto
            </label>
            <input
              id="f-monto"
              type="number"
              {...register('monto')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {errors.monto && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.monto.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="f-periodo">
              Período (YYYY-MM)
            </label>
            <input
              id="f-periodo"
              {...register('periodo')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="2024-03"
            />
            {errors.periodo && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.periodo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="f-detalle">
              Detalle (opcional)
            </label>
            <input
              id="f-detalle"
              {...register('detalle')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          {createMutation.isError && (
            <p role="alert" className="text-sm text-[#ba1a1a]">
              Error al registrar la factura. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-[#c4c6cd] px-4 py-2 text-sm text-[#43474c] hover:bg-[#f5f3f4]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
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
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AbonarForm>({
    resolver: zodResolver(abonarSchema),
    defaultValues: { fecha_pago: new Date().toISOString().slice(0, 10) },
  })

  const onSubmit = (data: AbonarForm) => {
    abonarMutation.mutate({ id: facturaId, fecha_pago: data.fecha_pago }, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl border border-[#c4c6cd]">
        <h2 className="mb-4 text-lg font-semibold text-primary">Marcar como abonada</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="ab-fecha">
              Fecha de pago
            </label>
            <input
              id="ab-fecha"
              type="date"
              {...register('fecha_pago')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {errors.fecha_pago && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.fecha_pago.message}
              </p>
            )}
          </div>
          {abonarMutation.isError && (
            <p role="alert" className="text-sm text-[#ba1a1a]">
              Error al abonar la factura. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-[#c4c6cd] px-4 py-2 text-sm text-[#43474c] hover:bg-[#f5f3f4]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={abonarMutation.isPending}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
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
  const estadoBadge: Record<
    FacturaEstado,
    { cls: string; dot: string; label: string }
  > = {
    Pendiente: {
      cls: 'bg-[#cce2fc] text-[#50657b]',
      dot: 'bg-[#4b6076]',
      label: 'Pendiente',
    },
    Abonada: {
      cls: 'bg-green-100 text-green-800',
      dot: 'bg-green-600',
      label: 'Abonada',
    },
  }

  const badge = estadoBadge[factura.estado]
  const initials = factura.usuario_id.slice(0, 2).toUpperCase()

  return (
    <tr
      className={`hover:bg-[#f5f3f4]/30 transition-colors ${
        factura.estado === 'Pendiente' ? '' : ''
      }`}
    >
      <td className="px-6 py-4">
        <span className="font-mono text-xs text-primary">{factura.id.slice(0, 12)}</span>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-[#efedef] flex items-center justify-center font-bold text-primary text-[10px]">
            {initials}
          </div>
          <div>
            <div className="font-medium text-sm text-primary leading-none">
              {factura.usuario_id.slice(0, 8)}
            </div>
            <div className="text-xs text-[#43474c] mt-0.5">{factura.detalle ?? '—'}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 text-sm text-[#43474c]">{factura.fecha_carga.slice(0, 10)}</td>
      <td className="px-6 py-4 text-sm text-[#43474c]">{factura.periodo}</td>
      <td className="px-6 py-4 font-medium text-sm text-primary">{fmt(factura.monto)}</td>
      <td className="px-6 py-4">
        <span
          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.cls}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
          {badge.label}
        </span>
      </td>
      <td className="px-6 py-4 text-right">
        <button
          className="p-1 text-[#43474c] hover:text-primary transition-colors active:scale-90"
          title="Descargar"
        >
          <Download className="w-4 h-4" />
        </button>
        {factura.estado === 'Pendiente' ? (
          <button
            onClick={() => onAbonar(factura.id)}
            className="ml-2 px-3 py-1 rounded bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700"
          >
            Abonar
          </button>
        ) : (
          <button className="ml-2 p-1 text-[#43474c] hover:text-primary transition-colors active:scale-90">
            <MoreVertical className="w-4 h-4" />
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

  const totalPendiente = items
    .filter((f) => f.estado === 'Pendiente')
    .reduce((s, f) => s + f.monto, 0)
  const totalAbonado = items
    .filter((f) => f.estado === 'Abonada')
    .reduce((s, f) => s + f.monto, 0)
  const vencidas = items.filter((f) => f.estado === 'Pendiente').length

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded-lg bg-[#ffdad6] p-4 text-[#93000a] border border-[#93000a]/20">
        Error al cargar las facturas. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-[#43474c] mb-1">
            <span>Finanzas</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-primary font-medium">Facturas</span>
          </nav>
          <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-primary">
            Gestión de Facturas
          </h1>
          <p className="text-[#43474c] text-sm mt-0.5">
            Seguimiento y gestión de facturación institucional.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 border border-[#c4c6cd] px-4 py-2 rounded-lg font-medium text-sm text-secondary hover:bg-[#efedef] transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filtrar</span>
          </button>
          <button className="flex items-center gap-1 border border-[#c4c6cd] px-4 py-2 rounded-lg font-medium text-sm text-secondary hover:bg-[#efedef] transition-colors">
            <FileDown className="w-4 h-4" />
            <span>Exportar CSV</span>
          </button>
          <button
            onClick={() => setShowNueva(true)}
            className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-lg font-medium text-sm hover:opacity-90 transition-all"
          >
            <ReceiptText className="w-4 h-4" />
            <span>Nueva Factura</span>
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-[#c4c6cd] p-6 rounded-xl">
          <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase mb-2">
            Total Pendiente
          </p>
          <h3 className="text-[28px] font-semibold text-primary leading-none">
            {fmt(totalPendiente)}
          </h3>
          <div className="mt-3 flex items-center gap-1 text-[#ba1a1a] text-xs font-medium">
            <TrendingUp className="w-3 h-3" />
            <span>Requiere seguimiento</span>
          </div>
        </div>
        <div className="bg-white border border-[#c4c6cd] p-6 rounded-xl">
          <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase mb-2">
            Cobrado (mes)
          </p>
          <h3 className="text-[28px] font-semibold text-primary leading-none">
            {fmt(totalAbonado)}
          </h3>
          <div className="mt-3 flex items-center gap-1 text-[#50657b] text-xs font-medium">
            <CheckCircle className="w-3 h-3" />
            <span>En línea con la meta</span>
          </div>
        </div>
        <div className="bg-white border border-[#c4c6cd] p-6 rounded-xl">
          <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase mb-2">
            Pendientes
          </p>
          <h3 className="text-[28px] font-semibold text-[#ba1a1a] leading-none">{vencidas}</h3>
          <div className="mt-3 flex items-center gap-1 text-[#43474c] text-xs font-medium">
            <AlertCircle className="w-3 h-3" />
            <span>Requiere auditoría</span>
          </div>
        </div>
        <div className="bg-primary text-white p-6 rounded-xl relative overflow-hidden">
          <div className="relative z-10">
            <p className="text-[11px] font-bold tracking-[0.05em] text-[#96a9be] uppercase mb-2">
              Próximo Vencimiento
            </p>
            <h3 className="text-[28px] font-semibold leading-none">—</h3>
            <p className="mt-3 text-xs opacity-80">Procesamiento batch activo.</p>
          </div>
          <Building2 className="absolute -right-4 -bottom-4 w-28 h-28 opacity-10" />
        </div>
      </div>

      {/* Filtros */}
      <form
        onSubmit={handleSubmit(onFiltrar)}
        className="flex flex-wrap gap-4 rounded-lg border border-[#c4c6cd] bg-[#f5f3f4] p-4"
      >
        <div>
          <label
            className="mb-1 block text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
            htmlFor="fl-usuario"
          >
            Usuario (ID)
          </label>
          <input
            id="fl-usuario"
            {...register('usuario_id')}
            className="rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="UUID"
          />
        </div>
        <div>
          <label
            className="mb-1 block text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
            htmlFor="fl-periodo"
          >
            Período
          </label>
          <input
            id="fl-periodo"
            {...register('periodo')}
            className="rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="2024-03"
          />
        </div>
        <div>
          <label
            className="mb-1 block text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
            htmlFor="fl-estado"
          >
            Estado
          </label>
          <select
            id="fl-estado"
            {...register('estado')}
            className="rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Todos</option>
            <option value="Pendiente">Pendiente</option>
            <option value="Abonada">Abonada</option>
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            className="rounded-lg border border-primary px-4 py-2 text-sm text-primary hover:bg-primary/5"
          >
            Filtrar
          </button>
        </div>
      </form>

      {/* Tabla */}
      <div className="bg-white border border-[#c4c6cd] rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#c4c6cd] flex justify-between items-center bg-[#f5f3f4]/50">
          <h4 className="font-medium text-sm text-primary">Facturas registradas</h4>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-xs text-[#43474c]">Todos los registros</span>
          </div>
        </div>

        {items.length === 0 ? (
          <p className="p-8 text-center text-sm text-[#43474c]">
            No hay facturas para los filtros seleccionados.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#c4c6cd] bg-[#f5f3f4]">
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    ID Factura
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    Entidad / Receptor
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    Fecha Carga
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    Período
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    Monto
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
                    Estado
                  </th>
                  <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase text-right">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#c4c6cd]">
                {items.map((f) => (
                  <FacturaRow key={f.id} factura={f} onAbonar={(id) => setAbonarId(id)} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Footer paginación */}
        <div className="px-6 py-4 border-t border-[#c4c6cd] flex justify-between items-center bg-white">
          <span className="text-xs text-[#43474c]">
            Mostrando 1 a {items.length} de {items.length} facturas
          </span>
          <div className="flex gap-1">
            <button className="px-2 py-1 border border-[#c4c6cd] rounded-lg text-xs text-[#43474c] hover:bg-[#efedef] transition-colors opacity-50 cursor-not-allowed">
              Anterior
            </button>
            <button className="px-3 py-1 bg-primary text-white rounded-lg font-medium text-xs">
              1
            </button>
            <button className="px-2 py-1 border border-[#c4c6cd] rounded-lg text-xs text-[#43474c] hover:bg-[#efedef] transition-colors">
              Siguiente
            </button>
          </div>
        </div>
      </div>

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
