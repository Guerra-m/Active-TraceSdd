import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Download, Users, Copy, TrendingUp, TrendingDown, Minus, MoreVertical } from 'lucide-react'
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

// ─── Shared styles ────────────────────────────────────────────────────────────

const inputCls = 'w-full rounded-lg border border-surface-subtle p-3 text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none bg-surface'
const labelCls = 'mb-1 block text-[11px] font-bold text-text-muted uppercase tracking-wider'
const errCls = 'mt-1 text-xs text-red-600'

// ─── Estado badge ─────────────────────────────────────────────────────────────

const ESTADO_BADGE: Record<string, string> = {
  vigente: 'bg-green-100 text-green-800',
  vencida: 'bg-red-100 text-red-800',
  futura: 'bg-blue-100 text-blue-800',
}

// ─── Vigencia Indicator ───────────────────────────────────────────────────────

function EstadoVigenciaIndicator({ estado }: { estado: string }) {
  switch (estado) {
    case 'vigente':
      return <div className="flex items-center gap-1 text-green-600"><TrendingUp className="w-4 h-4" /><span className="font-mono text-xs font-medium">Vigente</span></div>
    case 'vencida':
      return <div className="flex items-center gap-1 text-orange-600"><TrendingDown className="w-4 h-4" /><span className="font-mono text-xs font-medium">Vencida</span></div>
    default:
      return <div className="flex items-center gap-1 text-text-muted"><Minus className="w-4 h-4" /><span className="font-mono text-xs font-medium">Futura</span></div>
  }
}

// ─── AsignacionRow ────────────────────────────────────────────────────────────

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
  const initials = item.usuario_id.slice(0, 2).toUpperCase()

  return (
    <tr className={`hover:bg-surface-subtle transition-colors group ${isSelected ? 'bg-brand-50' : ''}`}>
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggle(item.id)}
          aria-label={`Seleccionar ${item.usuario_id}`}
          className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
        />
      </td>
      <td className="px-3 py-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs flex-shrink-0">
            {initials}
          </div>
          <div>
            <p className="text-sm font-semibold text-text">{item.rol}</p>
            <p className="font-mono text-xs text-text-muted">{item.usuario_id.slice(0, 8)}…</p>
          </div>
        </div>
      </td>
      <td className="px-3 py-3">
        <span className="px-2 py-0.5 bg-surface-muted border border-surface-subtle rounded text-xs text-text-muted">
          {item.rol}
        </span>
      </td>
      <td className="px-3 py-3">
        <div className="flex flex-wrap gap-1 max-w-xs">
          {item.comisiones.length > 0 ? (
            item.comisiones.slice(0, 2).map((c, i) => (
              <span key={i} className="px-2 py-0.5 bg-brand-50 text-brand-700 rounded-full text-[11px] font-medium border border-brand-100">
                {c}
              </span>
            ))
          ) : (
            <span className="text-xs text-text-muted">—</span>
          )}
        </div>
      </td>
      <td className="px-3 py-3">
        <span className={`px-2 py-0.5 text-[11px] font-bold rounded uppercase ${ESTADO_BADGE[item.estado_vigencia] ?? 'bg-slate-100 text-slate-600'}`}>
          {item.estado_vigencia}
        </span>
      </td>
      <td className="px-3 py-3">
        <EstadoVigenciaIndicator estado={item.estado_vigencia} />
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={() => onClonar(item)}
            className="p-1 text-text-muted hover:text-brand-600 hover:bg-surface-subtle rounded transition-colors"
            title="Clonar asignación"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button className="p-1 text-text-muted hover:text-text hover:bg-surface-subtle rounded transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

// ─── Modal Clonar ─────────────────────────────────────────────────────────────

function ClonarModal({ item, onClose }: { item: AsignacionItem; onClose: () => void }) {
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
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-1 text-lg font-semibold text-text">Clonar equipo: {item.rol}</h2>
        <p className="mb-4 font-mono text-xs text-text-muted">Cohorte origen: {item.cohorte_id ?? '—'}</p>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="cohorte_destino_id">ID Cohorte destino</label>
            <input id="cohorte_destino_id" {...register('cohorte_destino_id')} className={`${inputCls} font-mono`} placeholder="UUID de la cohorte destino" />
            {errors.cohorte_destino_id && <p role="alert" className={errCls}>{errors.cohorte_destino_id.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="desde">Fecha inicio</label>
            <input id="desde" type="date" {...register('desde')} className={inputCls} />
            {errors.desde && <p role="alert" className={errCls}>{errors.desde.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="hasta">Fecha fin (opcional)</label>
            <input id="hasta" type="date" {...register('hasta')} className={inputCls} />
          </div>
          {clonarMutation.isError && <p role="alert" className={errCls}>Error al clonar el equipo. Verificá los datos.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors">Cancelar</button>
            <button type="submit" disabled={clonarMutation.isPending} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors">
              {clonarMutation.isPending ? 'Clonando...' : 'Clonar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Modal Vigencia Bulk ──────────────────────────────────────────────────────

function VigenciaBulkModal({ items, onClose }: { items: AsignacionItem[]; onClose: () => void }) {
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
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-4 text-lg font-semibold text-text">Modificar vigencia ({items.length} asignaciones)</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="desde">Fecha inicio</label>
            <input id="desde" type="date" {...register('desde')} className={inputCls} />
            {errors.desde && <p role="alert" className={errCls}>{errors.desde.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="hasta">Fecha fin</label>
            <input id="hasta" type="date" {...register('hasta')} className={inputCls} />
          </div>
          {vigenciaMutation.isError && <p role="alert" className={errCls}>Error al modificar vigencia. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors">Cancelar</button>
            <button type="submit" disabled={vigenciaMutation.isPending} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors">
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
      <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Error al cargar los equipos. Intentá de nuevo.
      </div>
    )
  }

  const items = data ?? []
  const selectedItems = items.filter((i) => selectedIds.includes(i.id))
  const vigentes = items.filter((i) => i.estado_vigencia === 'vigente').length

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-text-muted mb-1">
            <span>Coordinación</span>
            <span className="mx-0.5">›</span>
            <span className="text-text font-medium">Equipos Docentes</span>
          </nav>
          <h2 className="text-2xl font-bold tracking-tight text-text">Equipos Docentes</h2>
        </div>
        <div className="flex gap-3">
          {selectedIds.length > 0 && (
            <button
              onClick={() => setShowVigenciaModal(true)}
              className="px-4 py-2 border border-surface-subtle bg-surface hover:bg-surface-subtle transition-colors rounded-lg flex items-center gap-2 text-sm font-medium"
            >
              Modificar vigencia ({selectedIds.length})
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="px-4 py-2 border border-surface-subtle bg-surface hover:bg-surface-subtle transition-colors rounded-lg flex items-center gap-2 text-sm font-medium disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-[11px] font-bold text-text-muted uppercase">Total</span>
            <Users className="w-4 h-4 text-text-muted" />
          </div>
          <p className="text-2xl font-bold text-text">{items.length}</p>
        </div>
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-[11px] font-bold text-text-muted uppercase">Vigentes</span>
            <TrendingUp className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-text">{vigentes}</p>
        </div>
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-[11px] font-bold text-text-muted uppercase">Seleccionados</span>
            <Copy className="w-4 h-4 text-text-muted" />
          </div>
          <p className="text-2xl font-bold text-text">{selectedIds.length}</p>
        </div>
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-[11px] font-bold text-text-muted uppercase">Vencidas</span>
            <TrendingDown className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-text">{items.filter((i) => i.estado_vigencia === 'vencida').length}</p>
        </div>
      </div>

      {/* Main Table */}
      {items.length === 0 ? (
        <div className="rounded-xl border border-surface-subtle bg-surface p-8 text-center">
          <p className="text-sm text-text-muted">No hay asignaciones registradas.</p>
        </div>
      ) : (
        <div className="bg-surface border border-surface-subtle rounded-xl overflow-hidden shadow-sm">
          {/* Toolbar */}
          <div className="px-4 py-3 border-b border-surface-subtle flex justify-between items-center bg-surface-muted">
            <span className="text-sm font-medium text-text">{items.length} miembros</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-surface border-b border-surface-subtle z-10">
                <tr>
                  <th className="px-4 py-3 w-10">
                    <input className="rounded border-slate-300 text-brand-600 focus:ring-brand-500" type="checkbox" />
                  </th>
                  <th className="px-3 py-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">Miembro</th>
                  <th className="px-3 py-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">Rol</th>
                  <th className="px-3 py-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">Comisiones</th>
                  <th className="px-3 py-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">Estado</th>
                  <th className="px-3 py-3 text-[11px] font-bold text-text-muted uppercase tracking-wider">Vigencia</th>
                  <th className="px-3 py-3 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-subtle">
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

          {/* Footer */}
          <div className="px-4 py-3 border-t border-surface-subtle bg-surface-muted">
            <span className="text-xs text-text-muted">
              Mostrando 1 a {items.length} de {items.length} entradas
            </span>
          </div>
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
