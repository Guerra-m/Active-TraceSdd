import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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

// ─── Modal genérico ABM ───────────────────────────────────────────────────────

function CarreraModal({
  carrera,
  onClose,
}: {
  carrera?: Carrera
  onClose: () => void
}) {
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
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{isEditing ? 'Editar' : 'Nueva'} carrera</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="c-nombre">Nombre</label>
            <input id="c-nombre" {...register('nombre')} className="w-full rounded border border-border p-2" />
            {errors.nombre && <p role="alert" className="mt-1 text-sm text-red-600">{errors.nombre.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="c-codigo">Código</label>
            <input id="c-codigo" {...register('codigo')} className="w-full rounded border border-border p-2" />
            {errors.codigo && <p role="alert" className="mt-1 text-sm text-red-600">{errors.codigo.message}</p>}
          </div>
          {isError && <p role="alert" className="text-sm text-red-600">Error al guardar. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border border-border px-4 py-2 text-sm">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CohorteModal({
  cohorte,
  carreras,
  onClose,
}: {
  cohorte?: Cohorte
  carreras: Carrera[]
  onClose: () => void
}) {
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
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{isEditing ? 'Editar' : 'Nueva'} cohorte</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="co-carrera">Carrera</label>
            <select id="co-carrera" {...register('carrera_id')} className="w-full rounded border border-border p-2">
              <option value="">Seleccioná...</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p role="alert" className="mt-1 text-sm text-red-600">{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="co-anio">Año</label>
            <input id="co-anio" type="number" {...register('anio')} className="w-full rounded border border-border p-2" />
            {errors.anio && <p role="alert" className="mt-1 text-sm text-red-600">{errors.anio.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="co-periodo">Período</label>
            <input id="co-periodo" {...register('periodo')} className="w-full rounded border border-border p-2" placeholder="Ej: 2024-1" />
            {errors.periodo && <p role="alert" className="mt-1 text-sm text-red-600">{errors.periodo.message}</p>}
          </div>
          {isError && <p role="alert" className="text-sm text-red-600">Error al guardar. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border border-border px-4 py-2 text-sm">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function MateriaModal({
  materia,
  carreras,
  onClose,
}: {
  materia?: Materia
  carreras: Carrera[]
  onClose: () => void
}) {
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
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{isEditing ? 'Editar' : 'Nueva'} materia</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="m-nombre">Nombre</label>
            <input id="m-nombre" {...register('nombre')} className="w-full rounded border border-border p-2" />
            {errors.nombre && <p role="alert" className="mt-1 text-sm text-red-600">{errors.nombre.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="m-codigo">Código</label>
            <input id="m-codigo" {...register('codigo')} className="w-full rounded border border-border p-2" />
            {errors.codigo && <p role="alert" className="mt-1 text-sm text-red-600">{errors.codigo.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="m-carrera">Carrera</label>
            <select id="m-carrera" {...register('carrera_id')} className="w-full rounded border border-border p-2">
              <option value="">Seleccioná...</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p role="alert" className="mt-1 text-sm text-red-600">{errors.carrera_id.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="m-grupo-plus">Grupo Plus (opcional)</label>
            <input id="m-grupo-plus" {...register('grupo_plus')} className="w-full rounded border border-border p-2" placeholder="Ej: G1" />
          </div>
          {isError && <p role="alert" className="text-sm text-red-600">Error al guardar. Intentá de nuevo.</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border border-border px-4 py-2 text-sm">Cancelar</button>
            <button type="submit" disabled={isPending} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Estructura académica</h1>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === t.id
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Carreras */}
      {tab === 'carreras' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setCarreraModal({ open: true })}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              + Nueva carrera
            </button>
          </div>
          {carreras?.length === 0 ? (
            <p className="text-gray-500">No hay carreras registradas.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-3 text-left">Nombre</th>
                    <th className="p-3 text-left">Código</th>
                    <th className="p-3 text-left">Estado</th>
                    <th className="p-3 text-left">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {carreras?.map((c) => (
                    <tr key={c.id} className="border-b border-border">
                      <td className="p-3 font-medium">{c.nombre}</td>
                      <td className="p-3">{c.codigo}</td>
                      <td className="p-3">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium ${c.activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                          {c.activa ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      <td className="p-3 flex gap-2">
                        <button onClick={() => setCarreraModal({ open: true, item: c })} className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50">Editar</button>
                        <button onClick={() => deleteCarreraMutation.mutate(c.id)} className="rounded border border-red-300 px-3 py-1 text-sm text-red-600 hover:bg-red-50">Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Cohortes */}
      {tab === 'cohortes' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setCohorteModal({ open: true })}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              + Nueva cohorte
            </button>
          </div>
          {cohortes?.length === 0 ? (
            <p className="text-gray-500">No hay cohortes registradas.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-3 text-left">Carrera</th>
                    <th className="p-3 text-left">Año</th>
                    <th className="p-3 text-left">Período</th>
                    <th className="p-3 text-left">Estado</th>
                    <th className="p-3 text-left">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {cohortes?.map((c) => (
                    <tr key={c.id} className="border-b border-border">
                      <td className="p-3 font-medium">{c.carrera_nombre}</td>
                      <td className="p-3">{c.anio}</td>
                      <td className="p-3">{c.periodo}</td>
                      <td className="p-3">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium ${c.activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                          {c.activa ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      <td className="p-3 flex gap-2">
                        <button onClick={() => setCohorteModal({ open: true, item: c })} className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50">Editar</button>
                        <button onClick={() => deleteCohorte.mutate(c.id)} className="rounded border border-red-300 px-3 py-1 text-sm text-red-600 hover:bg-red-50">Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Materias */}
      {tab === 'materias' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setMateriaModal({ open: true })}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              + Nueva materia
            </button>
          </div>
          {materias?.length === 0 ? (
            <p className="text-gray-500">No hay materias registradas.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-3 text-left">Nombre</th>
                    <th className="p-3 text-left">Código</th>
                    <th className="p-3 text-left">Carrera</th>
                    <th className="p-3 text-left">Grupo Plus</th>
                    <th className="p-3 text-left">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {materias?.map((m) => (
                    <tr key={m.id} className="border-b border-border">
                      <td className="p-3 font-medium">{m.nombre}</td>
                      <td className="p-3">{m.codigo}</td>
                      <td className="p-3">{m.carrera_nombre}</td>
                      <td className="p-3">{m.grupo_plus ?? '—'}</td>
                      <td className="p-3 flex gap-2">
                        <button onClick={() => setMateriaModal({ open: true, item: m })} className="rounded border border-border px-3 py-1 text-sm hover:bg-gray-50">Editar</button>
                        <button onClick={() => deleteMateria.mutate(m.id)} className="rounded border border-red-300 px-3 py-1 text-sm text-red-600 hover:bg-red-50">Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

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
