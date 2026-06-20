import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Download, Filter, Edit, XCircle, BookOpen, Calendar, BarChart3 } from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useCarreras,
  useCreateCarrera,
  useUpdateCarrera,
  usePatchCarreraEstado,
  useDeleteCarrera,
  useCohortes,
  useCreateCohorte,
  useDeleteCohorte,
  useMaterias,
  useCreateMateria,
  useUpdateMateria,
  usePatchMateriaEstado,
  useDeleteMateria,
} from '../hooks/useEstructura'
import type { Carrera, Cohorte, Materia, EstadoCarrera, EstadoMateria } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const carreraSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  codigo: z.string().min(1, 'El código es requerido'),
})

const cohorteSchema = z.object({
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  anio: z.coerce.number().int().min(2000, 'Año inválido'),
  vig_desde: z.string().min(1, 'La fecha de inicio es requerida'),
  vig_hasta: z.string().optional(),
})

const materiaSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  codigo: z.string().min(1, 'El código es requerido'),
  grupo_plus: z.string().optional(),
})

type CarreraForm = z.infer<typeof carreraSchema>
type CohorteForm = z.infer<typeof cohorteSchema>
type MateriaForm = z.infer<typeof materiaSchema>

// ─── Shared styles ────────────────────────────────────────────────────────────

const inputCls = 'w-full rounded-lg border border-surface-subtle p-3 text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none bg-surface'
const labelCls = 'mb-1 block text-[11px] font-bold text-text-muted uppercase tracking-wider'
const errCls = 'mt-1 text-xs text-red-600'

function EstadoBadge({ estado }: { estado: string }) {
  const isActiva = estado === 'Activa'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${isActiva ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'}`}>
      {estado.toUpperCase()}
    </span>
  )
}

// ─── CarreraModal ─────────────────────────────────────────────────────────────

function CarreraModal({ carrera, onClose }: { carrera?: Carrera; onClose: () => void }) {
  const createMutation = useCreateCarrera()
  const updateMutation = useUpdateCarrera()
  const patchEstado = usePatchCarreraEstado()
  const isEditing = Boolean(carrera)
  const isPending = createMutation.isPending || updateMutation.isPending || patchEstado.isPending
  const isError = createMutation.isError || updateMutation.isError || patchEstado.isError

  const [estadoLocal, setEstadoLocal] = useState<EstadoCarrera>(carrera?.estado ?? 'Activa')

  const { register, handleSubmit, formState: { errors } } = useForm<CarreraForm>({
    resolver: zodResolver(carreraSchema),
    defaultValues: carrera ? { nombre: carrera.nombre, codigo: carrera.codigo } : {},
  })

  const onSubmit = async (data: CarreraForm) => {
    if (isEditing && carrera) {
      await updateMutation.mutateAsync({ id: carrera.id, payload: data })
      if (estadoLocal !== carrera.estado) {
        await patchEstado.mutateAsync({ id: carrera.id, payload: { estado: estadoLocal } })
      }
      onClose()
    } else {
      await createMutation.mutateAsync(data)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-4 text-lg font-semibold text-text">{isEditing ? 'Editar' : 'Nueva'} carrera</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="c-nombre">Nombre</label>
            <input id="c-nombre" {...register('nombre')} className={inputCls} />
            {errors.nombre && <p role="alert" className={errCls}>{errors.nombre.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="c-codigo">Código</label>
            <input id="c-codigo" {...register('codigo')} className={`${inputCls} font-mono`} />
            {errors.codigo && <p role="alert" className={errCls}>{errors.codigo.message}</p>}
          </div>
          {isEditing && (
            <div>
              <label className={labelCls}>Estado</label>
              <div className="flex gap-2">
                {(['Activa', 'Inactiva'] as EstadoCarrera[]).map((e) => (
                  <button
                    key={e}
                    type="button"
                    onClick={() => setEstadoLocal(e)}
                    className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                      estadoLocal === e
                        ? e === 'Activa' ? 'bg-green-100 border-green-400 text-green-800' : 'bg-red-100 border-red-400 text-red-800'
                        : 'border-surface-subtle text-text-muted hover:bg-surface-subtle'
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}
          {isError && <p role="alert" className={errCls}>Error al guardar. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── CohorteModal ─────────────────────────────────────────────────────────────

function CohorteModal({ carreras, onClose }: { carreras: Carrera[]; onClose: () => void }) {
  const createMutation = useCreateCohorte()
  const isPending = createMutation.isPending
  const isError = createMutation.isError

  const { register, handleSubmit, formState: { errors } } = useForm<CohorteForm>({
    resolver: zodResolver(cohorteSchema),
    defaultValues: { anio: new Date().getFullYear() },
  })

  const onSubmit = (data: CohorteForm) => {
    createMutation.mutate(
      { ...data, vig_hasta: data.vig_hasta || null },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-4 text-lg font-semibold text-text">Nueva cohorte</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="co-carrera">Carrera</label>
            <select id="co-carrera" {...register('carrera_id')} className={inputCls}>
              <option value="">Seleccioná una carrera activa...</option>
              {carreras.filter((c) => c.estado === 'Activa').map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
            {errors.carrera_id && <p role="alert" className={errCls}>{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="co-nombre">Nombre</label>
            <input id="co-nombre" {...register('nombre')} placeholder="Ej: Cohorte 2024-1" className={inputCls} />
            {errors.nombre && <p role="alert" className={errCls}>{errors.nombre.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="co-anio">Año</label>
            <input id="co-anio" type="number" {...register('anio')} className={inputCls} />
            {errors.anio && <p role="alert" className={errCls}>{errors.anio.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls} htmlFor="co-desde">Vigencia desde</label>
              <input id="co-desde" type="date" {...register('vig_desde')} className={inputCls} />
              {errors.vig_desde && <p role="alert" className={errCls}>{errors.vig_desde.message}</p>}
            </div>
            <div>
              <label className={labelCls} htmlFor="co-hasta">Vigencia hasta (opcional)</label>
              <input id="co-hasta" type="date" {...register('vig_hasta')} className={inputCls} />
            </div>
          </div>
          {isError && <p role="alert" className={errCls}>Error al guardar. Verificá que la carrera esté activa.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── MateriaModal ─────────────────────────────────────────────────────────────

function MateriaModal({ materia, onClose }: { materia?: Materia; onClose: () => void }) {
  const createMutation = useCreateMateria()
  const updateMutation = useUpdateMateria()
  const patchEstado = usePatchMateriaEstado()
  const isEditing = Boolean(materia)
  const isPending = createMutation.isPending || updateMutation.isPending || patchEstado.isPending
  const isError = createMutation.isError || updateMutation.isError || patchEstado.isError

  const [estadoLocal, setEstadoLocal] = useState<EstadoMateria>(materia?.estado ?? 'Activa')

  const { register, handleSubmit, formState: { errors } } = useForm<MateriaForm>({
    resolver: zodResolver(materiaSchema),
    defaultValues: materia
      ? { nombre: materia.nombre, codigo: materia.codigo, grupo_plus: materia.grupo_plus ?? undefined }
      : {},
  })

  const onSubmit = async (data: MateriaForm) => {
    const payload = { ...data, grupo_plus: data.grupo_plus || null }
    if (isEditing && materia) {
      await updateMutation.mutateAsync({ id: materia.id, payload })
      if (estadoLocal !== materia.estado) {
        await patchEstado.mutateAsync({ id: materia.id, payload: { estado: estadoLocal } })
      }
      onClose()
    } else {
      await createMutation.mutateAsync(payload)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-4 text-lg font-semibold text-text">{isEditing ? 'Editar' : 'Nueva'} materia</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="m-nombre">Nombre</label>
            <input id="m-nombre" {...register('nombre')} className={inputCls} />
            {errors.nombre && <p role="alert" className={errCls}>{errors.nombre.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="m-codigo">Código</label>
            <input id="m-codigo" {...register('codigo')} className={`${inputCls} font-mono`} />
            {errors.codigo && <p role="alert" className={errCls}>{errors.codigo.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="m-grupo-plus">Grupo Plus (opcional)</label>
            <input id="m-grupo-plus" {...register('grupo_plus')} className={inputCls} placeholder="Ej: G1" />
          </div>
          {isEditing && (
            <div>
              <label className={labelCls}>Estado</label>
              <div className="flex gap-2">
                {(['Activa', 'Inactiva'] as EstadoMateria[]).map((e) => (
                  <button
                    key={e}
                    type="button"
                    onClick={() => setEstadoLocal(e)}
                    className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                      estadoLocal === e
                        ? e === 'Activa' ? 'bg-green-100 border-green-400 text-green-800' : 'bg-red-100 border-red-400 text-red-800'
                        : 'border-surface-subtle text-text-muted hover:bg-surface-subtle'
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}
          {isError && <p role="alert" className={errCls}>Error al guardar. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-surface-subtle px-4 py-2 text-sm hover:bg-surface-subtle transition-colors">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50 transition-colors">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

type ActiveTab = 'carreras' | 'cohortes' | 'materias'

function EstructuraContent() {
  const [tab, setTab] = useState<ActiveTab>('carreras')
  const [showFiltros, setShowFiltros] = useState(false)
  const [carreraModal, setCarreraModal] = useState<{ open: boolean; item?: Carrera }>({ open: false })
  const [cohorteModal, setCohorteModal] = useState(false)
  const [materiaModal, setMateriaModal] = useState<{ open: boolean; item?: Materia }>({ open: false })

  const { data: carreras, isLoading: loadingCarreras } = useCarreras()
  const { data: cohortes, isLoading: loadingCohortes } = useCohortes()
  const { data: materias, isLoading: loadingMaterias } = useMaterias()

  const deleteCarreraMutation = useDeleteCarrera()
  const deleteCohorteMutation = useDeleteCohorte()
  const deleteMateriaMutation = useDeleteMateria()

  // Map carrera_id → nombre for cohorte display
  const carreraMap = Object.fromEntries((carreras ?? []).map((c) => [c.id, c.nombre]))

  const isLoading = loadingCarreras || loadingCohortes || loadingMaterias

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  const tabs: { id: ActiveTab; label: string }[] = [
    { id: 'carreras', label: 'Carreras' },
    { id: 'cohortes', label: 'Cohortes' },
    { id: 'materias', label: 'Materias' },
  ]

  const onNewRecord = () => {
    if (tab === 'carreras') setCarreraModal({ open: true })
    else if (tab === 'cohortes') setCohorteModal(true)
    else setMateriaModal({ open: true })
  }

  const exportarEstructura = () => {
    let rows: string[]
    if (tab === 'carreras') {
      rows = ['Nombre,Código,Estado', ...(carreras ?? []).map((c) => `"${c.nombre}","${c.codigo}","${c.estado}"`)]
    } else if (tab === 'cohortes') {
      rows = ['Carrera,Nombre,Año,Desde,Hasta', ...(cohortes ?? []).map((c) => `"${carreraMap[c.carrera_id] ?? c.carrera_id}","${c.nombre}","${c.anio}","${c.vig_desde}","${c.vig_hasta ?? ''}"`)]
    } else {
      rows = ['Nombre,Código,Estado,Grupo Plus', ...(materias ?? []).map((m) => `"${m.nombre}","${m.codigo}","${m.estado}","${m.grupo_plus ?? ''}"`)]
    }
    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `estructura_${tab}_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const newLabel = { carreras: 'Nueva carrera', cohortes: 'Nueva cohorte', materias: 'Nueva materia' }[tab]

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <nav className="flex items-center gap-1 text-xs text-text-muted mb-1">
            <span>Académico</span>
            <span className="mx-0.5">›</span>
            <span className="text-text font-medium">Estructura Académica</span>
          </nav>
          <h2 className="text-2xl font-bold tracking-tight text-text">Estructura Académica</h2>
        </div>
        <button
          onClick={onNewRecord}
          className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          {newLabel}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-brand-600" />
            </div>
            <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">Total Materias</span>
          </div>
          <span className="text-2xl font-bold text-text">{materias?.length ?? 0}</span>
        </div>
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-amber-600" />
            </div>
            <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">Cohortes</span>
          </div>
          <span className="text-2xl font-bold text-text">{cohortes?.length ?? 0}</span>
        </div>
        <div className="bg-surface border border-surface-subtle p-4 rounded-xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-slate-600" />
            </div>
            <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">Carreras</span>
          </div>
          <span className="text-2xl font-bold text-text">{carreras?.length ?? 0}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center border-b border-surface-subtle">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-2 text-sm font-medium transition-colors ${
              tab === t.id
                ? 'border-b-2 border-brand-600 text-brand-700'
                : 'text-text-muted hover:text-text'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Table Container */}
      <div className="bg-surface border border-surface-subtle rounded-xl overflow-hidden shadow-sm">
        {/* Toolbar */}
        <div className="p-4 bg-surface-muted border-b border-surface-subtle flex items-center justify-between">
          <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">
            {tab === 'carreras' ? 'Carreras' : tab === 'cohortes' ? 'Cohortes' : 'Materias'}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowFiltros((v) => !v)}
              className={`flex items-center gap-1.5 px-3 py-1.5 border rounded text-xs transition-colors ${
                showFiltros
                  ? 'border-brand-600 bg-brand-50 text-brand-700'
                  : 'border-surface-subtle bg-surface text-text-muted hover:bg-surface-subtle'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />Filtrar
            </button>
            <button
              type="button"
              onClick={exportarEstructura}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-surface-subtle rounded bg-surface text-xs text-text-muted hover:bg-surface-subtle transition-colors"
            >
              <Download className="w-3.5 h-3.5" />Exportar
            </button>
          </div>
        </div>

        {/* Carreras */}
        {tab === 'carreras' && (
          !carreras || carreras.length === 0 ? (
            <div className="p-8 text-center text-sm text-text-muted">No hay carreras registradas.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-subtle border-b border-surface-subtle">
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Nombre</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Código</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle text-sm">
                  {carreras.map((c) => (
                    <tr key={c.id} className="hover:bg-surface-subtle transition-colors group">
                      <td className="px-4 py-3 font-medium text-text">{c.nombre}</td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-surface-muted px-1.5 py-0.5 rounded text-text-muted">{c.codigo}</span>
                      </td>
                      <td className="px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setCarreraModal({ open: true, item: c })} className="p-1 text-text-muted hover:text-brand-600 transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button onClick={() => deleteCarreraMutation.mutate(c.id)} className="p-1 text-text-muted hover:text-red-600 transition-colors">
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {/* Cohortes */}
        {tab === 'cohortes' && (
          !cohortes || cohortes.length === 0 ? (
            <div className="p-8 text-center text-sm text-text-muted">No hay cohortes registradas.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-subtle border-b border-surface-subtle">
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Nombre</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Carrera</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Año</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Desde</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Hasta</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle text-sm">
                  {cohortes.map((c) => (
                    <tr key={c.id} className="hover:bg-surface-subtle transition-colors group">
                      <td className="px-4 py-3 font-medium text-text">{c.nombre}</td>
                      <td className="px-4 py-3 text-text-muted">{carreraMap[c.carrera_id] ?? c.carrera_id.slice(0, 8)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-text-muted">{c.anio}</td>
                      <td className="px-4 py-3 text-text-muted">{c.vig_desde}</td>
                      <td className="px-4 py-3 text-text-muted">{c.vig_hasta ?? '—'}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => deleteCohorteMutation.mutate(c.id)} className="p-1 text-text-muted hover:text-red-600 transition-colors">
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {/* Materias */}
        {tab === 'materias' && (
          !materias || materias.length === 0 ? (
            <div className="p-8 text-center text-sm text-text-muted">No hay materias registradas.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-subtle border-b border-surface-subtle">
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Nombre</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Código</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Grupo Plus</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle text-sm">
                  {materias.map((m) => (
                    <tr key={m.id} className="hover:bg-surface-subtle transition-colors group">
                      <td className="px-4 py-3 font-medium text-text">{m.nombre}</td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-surface-muted px-1.5 py-0.5 rounded text-text-muted">{m.codigo}</span>
                      </td>
                      <td className="px-4 py-3 text-text-muted">{m.grupo_plus ?? '—'}</td>
                      <td className="px-4 py-3"><EstadoBadge estado={m.estado} /></td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setMateriaModal({ open: true, item: m })} className="p-1 text-text-muted hover:text-brand-600 transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button onClick={() => deleteMateriaMutation.mutate(m.id)} className="p-1 text-text-muted hover:text-red-600 transition-colors">
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {/* Footer */}
        <div className="p-4 bg-surface border-t border-surface-subtle">
          <span className="text-xs text-text-muted">
            Mostrando {tab === 'carreras' ? (carreras?.length ?? 0) : tab === 'cohortes' ? (cohortes?.length ?? 0) : (materias?.length ?? 0)} registros
          </span>
        </div>
      </div>

      {carreraModal.open && (
        <CarreraModal
          carrera={carreraModal.item}
          onClose={() => setCarreraModal({ open: false })}
        />
      )}

      {cohorteModal && (
        <CohorteModal
          carreras={carreras ?? []}
          onClose={() => setCohorteModal(false)}
        />
      )}

      {materiaModal.open && (
        <MateriaModal
          materia={materiaModal.item}
          onClose={() => setMateriaModal({ open: false })}
        />
      )}
    </div>
  )
}

export function EstructuraAcademicaPage() {
  return (
    <RequirePermission permission="estructura:gestionar">
      <EstructuraContent />
    </RequirePermission>
  )
}
