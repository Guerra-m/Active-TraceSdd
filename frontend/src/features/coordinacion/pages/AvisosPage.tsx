import { useState } from 'react'
import { CheckCheck, Archive } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import {
  useAvisos,
  useCreateAviso,
  useUpdateAviso,
  useDeleteAviso,
  useAckAviso,
} from '../hooks/useAvisos'
import type { Aviso, AvisoAlcance } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  severidad: z.enum(['Info', 'Advertencia', 'Crítico']),
  inicio_en: z.string().min(1, 'La fecha de inicio es requerida'),
  fin_en: z.string().optional(),
  activo: z.boolean(),
  requiere_ack: z.boolean(),
})

type AvisoForm = z.infer<typeof avisoSchema>

const ALCANCE_LABELS: Record<AvisoAlcance, string> = {
  Global: 'Global',
  PorMateria: 'Por materia',
  PorCohorte: 'Por cohorte',
  PorRol: 'Por rol',
}

// ─── Severity badge helpers ────────────────────────────────────────────────────

function getSeverityStyles(severidad: string) {
  switch (severidad) {
    case 'Crítico':
      return {
        bar: 'bg-error',
        badge: 'bg-error-container text-on-error-container',
        label: 'URGENTE',
      }
    case 'Advertencia':
      return {
        bar: 'bg-tertiary',
        badge: 'bg-tertiary-fixed text-on-tertiary-fixed',
        label: 'IMPORTANTE',
      }
    default:
      return {
        bar: 'bg-secondary',
        badge: 'bg-surface-container-high text-on-surface-variant',
        label: 'INFO',
      }
  }
}

// ─── AvisoCard ────────────────────────────────────────────────────────────────

function AvisoCard({
  aviso,
  onEdit,
}: {
  aviso: Aviso
  onEdit: (aviso: Aviso) => void
}) {
  const updateMutation = useUpdateAviso()
  const deleteMutation = useDeleteAviso()
  const ackMutation = useAckAviso()
  const styles = getSeverityStyles(aviso.severidad)

  return (
    <div className="bg-surface-container-lowest border border-outline-variant p-4 flex flex-col md:flex-row gap-6 group hover:border-primary transition-all duration-300">
      {/* Severity bar */}
      <div className={`flex-shrink-0 w-1 rounded-full ${styles.bar}`} />

      <div className="flex-1 min-w-0">
        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase ${styles.badge}`}>
            {styles.label}
          </span>
          <span className="font-mono text-[12px] text-on-surface-variant uppercase">
            {ALCANCE_LABELS[aviso.alcance]} · {aviso.inicio_en.slice(0, 10)}
          </span>
          {!aviso.activo && (
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold uppercase bg-surface-container text-on-surface-variant">
              INACTIVO
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-[16px] leading-6 font-medium text-primary mb-1">{aviso.titulo}</h3>

        {/* Body */}
        <p className="text-[14px] text-on-surface-variant mb-4 leading-relaxed">{aviso.cuerpo}</p>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {aviso.requiere_ack && (
            <button
              onClick={() => ackMutation.mutate(aviso.id)}
              disabled={ackMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 bg-secondary-container text-on-secondary-container rounded-lg text-[13px] font-medium hover:opacity-90 transition-all disabled:opacity-50"
            >
              <CheckCheck className="h-4 w-4" />
              Marcar como leído
            </button>
          )}
          {!aviso.activo ? (
            <button
              onClick={() => updateMutation.mutate({ id: aviso.id, payload: { activo: true } })}
              disabled={updateMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 border border-outline rounded-lg text-[13px] font-medium hover:bg-surface-container transition-all disabled:opacity-50"
            >
              Activar
            </button>
          ) : (
            <button
              onClick={() => updateMutation.mutate({ id: aviso.id, payload: { activo: false } })}
              disabled={updateMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 border border-outline rounded-lg text-[13px] font-medium hover:bg-surface-container transition-all disabled:opacity-50"
            >
              Desactivar
            </button>
          )}
          <button
            onClick={() => onEdit(aviso)}
            className="text-primary text-[13px] font-medium underline underline-offset-4 decoration-outline hover:decoration-primary transition-all px-2"
          >
            Editar
          </button>
          <button
            onClick={() => {
              if (confirm('¿Eliminar aviso?')) deleteMutation.mutate(aviso.id)
            }}
            className="text-error text-[13px] font-medium underline underline-offset-4 decoration-outline hover:decoration-error transition-all px-2"
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── AvisoModal ───────────────────────────────────────────────────────────────

function AvisoModal({
  aviso,
  onClose,
}: {
  aviso: Aviso | null
  onClose: () => void
}) {
  const createMutation = useCreateAviso()
  const updateMutation = useUpdateAviso()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AvisoForm>({
    resolver: zodResolver(avisoSchema),
    defaultValues: aviso
      ? {
          titulo: aviso.titulo,
          cuerpo: aviso.cuerpo,
          alcance: aviso.alcance,
          severidad: aviso.severidad,
          inicio_en: aviso.inicio_en.slice(0, 16),
          fin_en: aviso.fin_en?.slice(0, 16) ?? undefined,
          activo: aviso.activo,
          requiere_ack: aviso.requiere_ack,
        }
      : { alcance: 'Global', severidad: 'Info', activo: true, requiere_ack: false },
  })

  const isEditing = !!aviso
  const isPending = createMutation.isPending || updateMutation.isPending
  const isError = createMutation.isError || updateMutation.isError

  const onSubmit = (data: AvisoForm) => {
    if (isEditing) {
      updateMutation.mutate({ id: aviso.id, payload: data }, { onSuccess: onClose })
    } else {
      createMutation.mutate(data, { onSuccess: onClose })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-surface-container-lowest p-6 shadow-xl border border-outline-variant">
        <h2 className="mb-4 text-[20px] leading-7 font-semibold text-primary">
          {isEditing ? 'Editar aviso' : 'Nuevo aviso'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-titulo">
              Título
            </label>
            <input
              id="av-titulo"
              {...register('titulo')}
              className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.titulo && (
              <p role="alert" className="mt-1 text-[13px] text-error">
                {errors.titulo.message}
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-cuerpo">
              Cuerpo
            </label>
            <textarea
              id="av-cuerpo"
              {...register('cuerpo')}
              rows={4}
              className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.cuerpo && (
              <p role="alert" className="mt-1 text-[13px] text-error">
                {errors.cuerpo.message}
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-alcance">
                Alcance
              </label>
              <select
                id="av-alcance"
                {...register('alcance')}
                className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {Object.entries(ALCANCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-severidad">
                Severidad
              </label>
              <select
                id="av-severidad"
                {...register('severidad')}
                className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="Info">Info</option>
                <option value="Advertencia">Advertencia</option>
                <option value="Crítico">Crítico</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-inicio">
                Desde
              </label>
              <input
                id="av-inicio"
                type="datetime-local"
                {...register('inicio_en')}
                className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
              />
              {errors.inicio_en && (
                <p role="alert" className="mt-1 text-[13px] text-error">
                  {errors.inicio_en.message}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-[13px] font-medium text-on-surface-variant" htmlFor="av-fin">
                Hasta (opcional)
              </label>
              <input
                id="av-fin"
                type="datetime-local"
                {...register('fin_en')}
                className="w-full rounded border border-outline-variant bg-surface-container-low px-3 py-2 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <input id="av-activo" type="checkbox" {...register('activo')} className="rounded border-outline-variant" />
              <label className="text-[14px] text-on-surface" htmlFor="av-activo">
                Activo
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input id="av-ack" type="checkbox" {...register('requiere_ack')} className="rounded border-outline-variant" />
              <label className="text-[14px] text-on-surface" htmlFor="av-ack">
                Requiere confirmación
              </label>
            </div>
          </div>
          {isError && (
            <p role="alert" className="text-[13px] text-error">
              Error al guardar el aviso. Intentá de nuevo.
            </p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-outline-variant px-4 py-2 text-[14px] font-medium hover:bg-surface-container transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="rounded bg-primary px-4 py-2 text-[14px] font-medium text-on-primary hover:opacity-90 transition-colors disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function AvisosContent() {
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Aviso | null>(null)
  const [mostrarArchivados, setMostrarArchivados] = useState(false)

  const { data, isLoading, isError } = useAvisos()
  const todosLosItems = data ?? []
  const items = mostrarArchivados
    ? todosLosItems.filter((a) => !a.activo)
    : todosLosItems.filter((a) => a.activo)

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded-lg bg-error-container border border-error/20 p-4 text-[14px] text-on-error-container">
        Error al cargar los avisos. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <nav className="flex items-center gap-1 mb-1 text-[13px] text-on-surface-variant">
            <span>Académico</span>
            <span className="text-outline mx-1">/</span>
            <span className="font-medium text-primary">Avisos</span>
          </nav>
          <h1 className="text-[30px] leading-[38px] tracking-tight font-semibold text-primary">
            Avisos institucionales
          </h1>
          <p className="text-[14px] text-on-surface-variant mt-1">
            Mantené informados a los alumnos con las últimas novedades.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMostrarArchivados((v) => !v)}
            className={`px-4 py-2 border rounded-lg text-[13px] font-medium transition-all ${
              mostrarArchivados
                ? 'border-primary bg-primary-container text-on-primary-container'
                : 'border-outline hover:bg-surface-container'
            }`}
          >
            <Archive className="h-4 w-4 inline mr-1.5" />
            {mostrarArchivados ? 'Ver activos' : 'Archivados'}
          </button>
          <button
            onClick={() => {
              setEditTarget(null)
              setShowModal(true)
            }}
            className="px-4 py-2 bg-primary text-on-primary rounded-lg text-[13px] font-medium hover:opacity-90 transition-all"
          >
            Nuevo aviso
          </button>
        </div>
      </div>

      {/* Notice list */}
      {items.length === 0 ? (
        <p className="text-[14px] text-on-surface-variant">
          {mostrarArchivados ? 'No hay avisos archivados.' : 'No hay avisos publicados.'}
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {items.map((aviso) => (
            <AvisoCard
              key={aviso.id}
              aviso={aviso}
              onEdit={(a) => {
                setEditTarget(a)
                setShowModal(true)
              }}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AvisoModal
          aviso={editTarget}
          onClose={() => {
            setShowModal(false)
            setEditTarget(null)
          }}
        />
      )}
    </div>
  )
}

export function AvisosPage() {
  return (
    <RequirePermission permission="avisos:publicar">
      <AvisosContent />
    </RequirePermission>
  )
}
