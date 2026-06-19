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
  useDeleteCarrera,
  useCohortes,
  useCreateCohorte,
  useUpdateCohorte,
  useDeleteCohorte,
  useMaterias,
  useCreateMateria,
  useUpdateMateria,
  useDeleteMateria,
} from '../hooks/useEstructura'
import type { Carrera, Cohorte, Materia } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const carreraSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  codigo: z.string().min(1, 'El código es requerido'),
  activa: z.boolean().optional(),
})

const cohorteSchema = z.object({
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  anio: z.coerce.number().int().min(2000, 'Año inválido'),
  periodo: z.string().min(1, 'El período es requerido'),
  activa: z.boolean().optional(),
})

const materiaSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  codigo: z.string().min(1, 'El código es requerido'),
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  grupo_plus: z.string().optional(),
  activa: z.boolean().optional(),
})

type CarreraForm = z.infer<typeof carreraSchema>
type CohorteForm = z.infer<typeof cohorteSchema>
type MateriaForm = z.infer<typeof materiaSchema>

// ─── Shared input styles ──────────────────────────────────────────────────────

const inputCls = 'w-full rounded-lg border border-surface-subtle p-3 text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none bg-surface'
const labelCls = 'mb-1 block text-[11px] font-bold text-text-muted uppercase tracking-wider'
const errCls = 'mt-1 text-xs text-red-600'

// ─── Modals ───────────────────────────────────────────────────────────────────

function CarreraModal({ carrera, onClose }: { carrera?: Carrera; onClose: () => void }) {
  const createMutation = useCreateCarrera()
  const updateMutation = useUpdateCarrera()
  const isEditing = Boolean(carrera)
  const isPending = isEditing ? updateMutation.isPending : createMutation.isPending
  const isError = isEditing ? updateMutation.isError : createMutation.isError

  const { register, handleSubmit, formState: { errors } } = useForm<CarreraForm>({
    resolver: zodResolver(carreraSchema),
    defaultValues: carrera ? { nombre: carrera.nombre, codigo: carrera.codigo, activa: carrera.activa } : {},
  })

  const onSubmit = (data: CarreraForm) => {
    if (isEditing && carrera) {
      updateMutation.mutate({ id: carrera.id, payload: data }, { onSuccess: onClose })
    } else {
      createMutation.mutate(data, { onSuccess: onClose })
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

function CohorteModal({ cohorte, carreras, onClose }: { cohorte?: Cohorte; carreras: Carrera[]; onClose: () => void }) {
  const createMutation = useCreateCohorte()
  const updateMutation = useUpdateCohorte()
  const isEditing = Boolean(cohorte)
  const isPending = isEditing ? updateMutation.isPending : createMutation.isPending
  const isError = isEditing ? updateMutation.isError : createMutation.isError

  const { register, handleSubmit, formState: { errors } } = useForm<CohorteForm>({
    resolver: zodResolver(cohorteSchema),
    defaultValues: cohorte
      ? { carrera_id: cohorte.carrera_id, anio: cohorte.anio, periodo: cohorte.periodo, activa: cohorte.activa }
      : {},
  })

  const onSubmit = (data: CohorteForm) => {
    if (isEditing && cohorte) {
      updateMutation.mutate({ id: cohorte.id, payload: data }, { onSuccess: onClose })
    } else {
      createMutation.mutate(data, { onSuccess: onClose })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl border border-surface-subtle">
        <h2 className="mb-4 text-lg font-semibold text-text">{isEditing ? 'Editar' : 'Nueva'} cohorte</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className={labelCls} htmlFor="co-carrera">Carrera</label>
            <select id="co-carrera" {...register('carrera_id')} className={inputCls}>
              <option value="">Seleccioná...</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p role="alert" className={errCls}>{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="co-anio">Año</label>
            <input id="co-anio" type="number" {...register('anio')} className={inputCls} />
            {errors.anio && <p role="alert" className={errCls}>{errors.anio.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="co-periodo">Período</label>
            <input id="co-periodo" {...register('periodo')} className={inputCls} placeholder="Ej: 2024-1" />
            {errors.periodo && <p role="alert" className={errCls}>{errors.periodo.message}</p>}
          </div>
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

function MateriaModal({ materia, carreras, onClose }: { materia?: Materia; carreras: Carrera[]; onClose: () => void }) {
  const createMutation = useCreateMateria()
  const updateMutation = useUpdateMateria()
  const isEditing = Boolean(materia)
  const isPending = isEditing ? updateMutation.isPending : createMutation.isPending
  const isError = isEditing ? updateMutation.isError : createMutation.isError

  const { register, handleSubmit, formState: { errors } } = useForm<MateriaForm>({
    resolver: zodResolver(materiaSchema),
    defaultValues: materia
      ? { nombre: materia.nombre, codigo: materia.codigo, carrera_id: materia.carrera_id, grupo_plus: materia.grupo_plus ?? undefined }
      : {},
  })

  const onSubmit = (data: MateriaForm) => {
    if (isEditing && materia) {
      updateMutation.mutate({ id: materia.id, payload: data }, { onSuccess: onClose })
    } else {
      createMutation.mutate(data, { onSuccess: onClose })
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
            <label className={labelCls} htmlFor="m-carrera">Carrera</label>
            <select id="m-carrera" {...register('carrera_id')} className={inputCls}>
              <option value="">Seleccioná...</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p role="alert" className={errCls}>{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className={labelCls} htmlFor="m-grupo-plus">Grupo Plus (opcional)</label>
            <input id="m-grupo-plus" {...register('grupo_plus')} className={inputCls} placeholder="Ej: G1" />
          </div>
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
  const [carreraModal, setCarreraModal] = useState<{ open: boolean; item?: Carrera }>({ open: false })
  const [cohorteModal, setCohorteModal] = useState<{ open: boolean; item?: Cohorte }>({ open: false })
  const [materiaModal, setMateriaModal] = useState<{ open: boolean; item?: Materia }>({ open: false })

  const { data: carreras, isLoading: loadingCarreras } = useCarreras()
  const { data: cohortes, isLoading: loadingCohortes } = useCohortes()
  const { data: materias, isLoading: loadingMaterias } = useMaterias()

  const deleteCarreraMutation = useDeleteCarrera()
  const deleteCohorte = useDeleteCohorte()
  const deleteMateria = useDeleteMateria()

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
    else if (tab === 'cohortes') setCohorteModal({ open: true })
    else setMateriaModal({ open: true })
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
            <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">Cohortes Activas</span>
          </div>
          <span className="text-2xl font-bold text-text">{cohortes?.filter((c) => c.activa).length ?? 0}</span>
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
            <button className="flex items-center gap-1.5 px-3 py-1.5 border border-surface-subtle rounded bg-surface text-xs text-text-muted hover:bg-surface-subtle transition-colors">
              <Filter className="w-3.5 h-3.5" />Filtrar
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 border border-surface-subtle rounded bg-surface text-xs text-text-muted hover:bg-surface-subtle transition-colors">
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
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${c.activa ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'}`}>
                          {c.activa ? 'ACTIVA' : 'INACTIVA'}
                        </span>
                      </td>
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
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Carrera</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Año</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Período</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle text-sm">
                  {cohortes.map((c) => (
                    <tr key={c.id} className="hover:bg-surface-subtle transition-colors group">
                      <td className="px-4 py-3 font-medium text-text">{c.carrera_nombre}</td>
                      <td className="px-4 py-3 font-mono text-xs text-text-muted">{c.anio}</td>
                      <td className="px-4 py-3 text-text-muted">{c.periodo}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${c.activa ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'}`}>
                          {c.activa ? 'ACTIVA' : 'INACTIVA'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setCohorteModal({ open: true, item: c })} className="p-1 text-text-muted hover:text-brand-600 transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button onClick={() => deleteCohorte.mutate(c.id)} className="p-1 text-text-muted hover:text-red-600 transition-colors">
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
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Carrera</th>
                    <th className="px-4 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">Grupo Plus</th>
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
                      <td className="px-4 py-3 text-text-muted">{m.carrera_nombre}</td>
                      <td className="px-4 py-3 text-text-muted">{m.grupo_plus ?? '—'}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setMateriaModal({ open: true, item: m })} className="p-1 text-text-muted hover:text-brand-600 transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button onClick={() => deleteMateria.mutate(m.id)} className="p-1 text-text-muted hover:text-red-600 transition-colors">
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

      {cohorteModal.open && (
        <CohorteModal
          cohorte={cohorteModal.item}
          carreras={carreras ?? []}
          onClose={() => setCohorteModal({ open: false })}
        />
      )}

      {materiaModal.open && (
        <MateriaModal
          materia={materiaModal.item}
          carreras={carreras ?? []}
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
