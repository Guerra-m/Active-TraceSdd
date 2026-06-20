import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  BarChart3,
  Activity,
  Gauge,
  Download,
  Pencil,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Plus,
} from 'lucide-react'
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

// ─── Helpers ──────────────────────────────────────────────────────────────────

const PAGE_SIZE_SAL = 10

const fmt = (n: number) =>
  n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })

function exportarGrillaCSV(
  base: SalarioBase[],
  plus: SalarioPlus[],
) {
  const rows = [
    'Tipo,Rol,Monto,Desde,Hasta',
    ...base.map((s) => `"base","${s.rol}","${s.monto}","${s.desde}","${s.hasta ?? ''}"`),
    ...plus.map((s) => `"plus","${s.rol}","${s.monto}","${s.desde}","${s.hasta ?? ''}"`),
  ].join('\n')
  const blob = new Blob([rows], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `grilla_salarial_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

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
        updateBase.mutate({ id: salario.id, payload: data }, { onSuccess: onClose })
      } else {
        createBase.mutate(data, { onSuccess: onClose })
      }
    } else {
      if (isEditing && salario) {
        updatePlus.mutate({ id: salario.id, payload: data }, { onSuccess: onClose })
      } else {
        createPlus.mutate(data, { onSuccess: onClose })
      }
    }
  }

  const titulo = `${isEditing ? 'Editar' : 'Nuevo'} salario ${tipo === 'base' ? 'base' : 'plus'}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl border border-[#c4c6cd]">
        <h2 className="mb-4 text-lg font-semibold text-primary">{titulo}</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="s-rol">
              Rol
            </label>
            <input
              id="s-rol"
              {...register('rol')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Ej: TUTOR"
            />
            {errors.rol && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.rol.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="s-monto">
              Monto
            </label>
            <input
              id="s-monto"
              type="number"
              {...register('monto')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="80000"
            />
            {errors.monto && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.monto.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="s-desde">
              Desde
            </label>
            <input
              id="s-desde"
              type="date"
              {...register('desde')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {errors.desde && (
              <p role="alert" className="mt-1 text-xs text-[#ba1a1a]">
                {errors.desde.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1b1c1d]" htmlFor="s-hasta">
              Hasta (opcional)
            </label>
            <input
              id="s-hasta"
              type="date"
              {...register('hasta')}
              className="w-full rounded-lg border border-[#c4c6cd] p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          {isError && (
            <p role="alert" className="text-sm text-[#ba1a1a]">
              Error al guardar el salario. Intentá de nuevo.
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
              disabled={isPending}
              className="rounded-lg bg-primary px-4 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
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
  const [page, setPage] = useState(0)
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE_SAL))
  const pagedItems = items.slice(page * PAGE_SIZE_SAL, (page + 1) * PAGE_SIZE_SAL)

  return (
    <div className="bg-white border border-[#c4c6cd] rounded-xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-[#c4c6cd] flex justify-between items-center bg-white">
        <h3 className="font-medium text-sm text-primary">{titulo}</h3>
        <button
          onClick={onNuevo}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-lg hover:opacity-90 transition-opacity"
        >
          <Plus className="w-3 h-3" />
          Nuevo
        </button>
      </div>

      {items.length === 0 ? (
        <p className="p-6 text-sm text-[#43474c]">No hay registros de salario {tipo}.</p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead className="bg-white">
                <tr className="text-[#43474c] border-b border-[#c4c6cd]">
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    Rol / ID
                  </th>
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    Monto (base)
                  </th>
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    Desde
                  </th>
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    Hasta
                  </th>
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    Estado
                  </th>
                  <th className="text-[11px] font-bold tracking-[0.05em] px-6 py-4 uppercase">
                    {tipo === 'base' ? 'Variación' : 'Factor'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {pagedItems.map((s, idx) => (
                  <tr
                    key={s.id}
                    className={`hover:bg-[#cce2fc]/10 transition-colors group cursor-pointer ${
                      idx % 2 === 0 ? '' : 'bg-[#f1f5f9]'
                    }`}
                    onClick={() => onEditar(s)}
                  >
                    <td className="px-6 py-4 font-mono text-xs text-primary font-medium">
                      {s.rol}
                    </td>
                    <td className="px-6 py-4 font-mono text-sm">{fmt(s.monto)}</td>
                    <td className="px-6 py-4 text-sm text-[#43474c]">{s.desde}</td>
                    <td className="px-6 py-4 text-sm text-[#43474c]">{s.hasta ?? '—'}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            s.hasta ? 'bg-[#c4c6cd]' : 'bg-green-500'
                          }`}
                        />
                        <span className="text-xs text-[#43474c]">
                          {s.hasta ? 'Histórico' : 'Activo'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded font-mono text-[11px]">
                          Vigente
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onEditar(s)
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                          title="Editar"
                        >
                          <Pencil className="w-3.5 h-3.5 text-[#43474c] hover:text-primary" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-4 bg-[#f5f3f4] border-t border-[#c4c6cd] flex justify-between items-center">
            <p className="text-xs text-[#43474c]">
              Mostrando {pagedItems.length} de {items.length} registros — página {page + 1} de {totalPages}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="w-8 h-8 flex items-center justify-center border border-[#c4c6cd] rounded hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4 text-[#43474c]" />
              </button>
              <button className="w-8 h-8 flex items-center justify-center bg-primary text-white rounded text-xs font-medium">
                {page + 1}
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="w-8 h-8 flex items-center justify-center border border-[#c4c6cd] rounded hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4 text-[#43474c]" />
              </button>
            </div>
          </div>
        </>
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

  const baseItems = salariosBase ?? []
  const plusItems = salariosPlus ?? []

  const totalAnual = baseItems.reduce((s, b) => s + b.monto * 12, 0)
  const promedioBase = baseItems.length > 0 ? baseItems.reduce((s, b) => s + b.monto, 0) / baseItems.length : 0
  const bonusUso = plusItems.length > 0 ? Math.min(100, (plusItems.length / 10) * 100) : 0

  if (loadingBase || loadingPlus) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-[#43474c] mb-1">
            <span>Configuración institucional</span>
            <ChevronRight className="w-3 h-3" />
            <span>Liquidaciones</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-primary font-medium">Grilla Salarial</span>
          </nav>
          <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-primary">
            Grilla Salarial
          </h1>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => exportarGrillaCSV(baseItems, plusItems)}
            disabled={baseItems.length === 0 && plusItems.length === 0}
            className="px-4 py-2 bg-white border border-[#c4c6cd] text-primary font-medium rounded hover:bg-[#f5f3f4] transition-colors flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Exportar CSV
          </button>
          <button
            onClick={() => setModal({ tipo: 'base' })}
            className="px-4 py-2 bg-primary text-white font-medium rounded hover:opacity-90 transition-opacity flex items-center gap-2 text-sm shadow-sm"
          >
            <Pencil className="w-4 h-4" />
            Nuevo salario base
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1 bg-white border border-[#c4c6cd] p-4 rounded-xl">
          <div className="flex justify-between items-start mb-2">
            <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
              Total Anual Planilla
            </p>
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <p className="font-mono text-2xl font-bold text-primary">{fmt(totalAnual)}</p>
          <div className="flex items-center gap-1 mt-2 text-green-700">
            <TrendingUp className="w-3 h-3" />
            <span className="text-xs">Proyección anual</span>
          </div>
        </div>
        <div className="col-span-1 bg-white border border-[#c4c6cd] p-4 rounded-xl">
          <div className="flex justify-between items-start mb-2">
            <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
              Promedio Salario Base
            </p>
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <p className="font-mono text-2xl font-bold text-primary">{fmt(promedioBase)}</p>
          <p className="text-xs text-[#43474c] mt-2">
            Calculado sobre {baseItems.length} registros
          </p>
        </div>
        <div className="col-span-1 bg-white border border-[#c4c6cd] p-4 rounded-xl">
          <div className="flex justify-between items-start mb-2">
            <p className="text-[11px] font-bold tracking-[0.05em] text-[#43474c] uppercase">
              Registros Plus
            </p>
            <Gauge className="w-5 h-5 text-primary" />
          </div>
          <p className="font-mono text-2xl font-bold text-primary">{plusItems.length}</p>
          <div className="w-full bg-[#efedef] h-1.5 rounded-full mt-2">
            <div
              className="bg-primary h-full rounded-full transition-all"
              style={{ width: `${bonusUso}%` }}
            />
          </div>
        </div>
      </div>

      {/* Tabla Base */}
      <SalariosTable
        titulo="Matriz de Salario Base"
        tipo="base"
        items={baseItems}
        onNuevo={() => setModal({ tipo: 'base' })}
        onEditar={(s) => setModal({ tipo: 'base', salario: s as SalarioBase })}
      />

      {/* Tabla Plus */}
      <SalariosTable
        titulo="Estructura de Plus / Bonus"
        tipo="plus"
        items={plusItems}
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
