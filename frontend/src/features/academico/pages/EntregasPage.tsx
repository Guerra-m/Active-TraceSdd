import { Download, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { useEntregasSinCorregir } from '../hooks/useEntregas'
import type { EntregaSinCorregir } from '../types'

interface EntregasPageProps {
  asignacionId: string
  materiaId: string
}

function exportarCSV(entregas: EntregaSinCorregir[]) {
  const headers = ['Nombre', 'Apellidos', 'Actividad', 'Importado el']
  const rows = entregas.map((e) => [
    e.nombre,
    e.apellidos,
    e.actividad,
    new Date(e.importado_at).toLocaleDateString('es-AR'),
  ])
  const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'entregas-sin-corregir.csv'
  link.click()
  URL.revokeObjectURL(url)
}

// ─── Initials avatar ─────────────────────────────────────────────────────────

const AVATAR_BG = [
  'bg-primary-fixed text-primary',
  'bg-secondary-fixed text-secondary',
  'bg-tertiary-fixed text-tertiary',
  'bg-primary-fixed-dim text-primary',
  'bg-secondary-fixed-dim text-secondary',
]

function Avatar({ nombre, apellidos, index }: { nombre: string; apellidos: string; index: number }) {
  const initials = `${nombre.charAt(0)}${apellidos.charAt(0)}`.toUpperCase()
  return (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${AVATAR_BG[index % AVATAR_BG.length]}`}
    >
      {initials}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function EntregasPage({ asignacionId, materiaId }: EntregasPageProps) {
  const { data: resp, isLoading, isError } = useEntregasSinCorregir(asignacionId, materiaId)

  const sinContexto = !asignacionId || !materiaId
  const entregas = resp?.items ?? []
  const sinEntregas = entregas.length === 0

  // Compute a simple "progress": items without a grade are pending
  const totalEntregas = entregas.length

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <nav className="flex items-center gap-1 mb-2 text-[13px] text-on-surface-variant">
            <span>Materia</span>
            <span className="text-outline mx-1">/</span>
            <span className="font-semibold text-primary">Detalle</span>
          </nav>
          <h2 className="text-[30px] leading-[38px] tracking-tight font-semibold text-on-background">
            Entregas sin corregir
          </h2>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={sinEntregas}
            onClick={() => exportarCSV(entregas)}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-[14px] font-medium hover:bg-surface-container-low transition-colors disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download className="h-5 w-5" />
            Exportar reporte
          </button>
        </div>
      </div>

      {sinContexto && (
        <p className="text-[14px] text-on-surface-variant">No hay asignación seleccionada.</p>
      )}

      {!sinContexto && (
        <>
          {/* Summary cards */}
          {!isLoading && !isError && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <AlertCircle className="h-5 w-5 text-primary" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Pendientes</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[30px] leading-[38px] font-semibold text-on-surface">
                    {totalEntregas}
                  </span>
                  <span className="text-[13px] text-on-surface-variant">sin corregir</span>
                </div>
              </div>
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <Clock className="h-5 w-5 text-secondary" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Más reciente</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[14px] font-medium text-on-surface">
                    {totalEntregas > 0
                      ? new Date(
                          entregas.reduce((a, b) =>
                            new Date(a.importado_at) > new Date(b.importado_at) ? a : b
                          ).importado_at
                        ).toLocaleDateString('es-AR')
                      : '—'}
                  </span>
                </div>
              </div>
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Actividades distintas</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[30px] leading-[38px] font-semibold text-on-surface">
                    {new Set(entregas.map((e) => e.actividad)).size}
                  </span>
                </div>
              </div>
            </div>
          )}

          {isLoading && (
            <p className="text-[14px] text-on-surface-variant">Cargando entregas...</p>
          )}
          {isError && (
            <p className="text-[14px] text-error">Error al cargar las entregas.</p>
          )}

          {!isLoading && !isError && sinEntregas && (
            <p className="text-[14px] text-on-surface-variant">No hay entregas pendientes de corrección.</p>
          )}

          {/* Activity log table */}
          {entregas.length > 0 && (
            <section className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-lowest">
                <div className="flex items-center gap-6">
                  <h2 className="text-[20px] leading-7 font-semibold text-primary">
                    Registro de actividades
                  </h2>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low border-b border-outline-variant">
                      <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                        Alumno
                      </th>
                      <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                        Actividad
                      </th>
                      <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                        Fecha de entrega
                      </th>
                      <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                        Estado
                      </th>
                      <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant text-right">
                        Nota
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-[13px]">
                    {entregas.map((e, i) => (
                      <tr
                        key={`${e.entrada_padron_id}-${e.actividad}-${i}`}
                        className="group hover:bg-secondary-container/10 transition-colors border-b border-outline-variant last:border-0"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Avatar nombre={e.nombre} apellidos={e.apellidos} index={i} />
                            <span className="font-medium text-on-surface">
                              {e.apellidos}, {e.nombre}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-bold text-primary">{e.actividad}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-on-surface-variant">
                          {new Date(e.importado_at).toLocaleDateString('es-AR')}
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1 w-fit">
                            <AlertCircle className="h-3.5 w-3.5" />
                            Pendiente
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-mono text-on-surface-variant">--</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-surface-container-low border-t border-outline-variant flex justify-between items-center">
                <p className="text-[11px] text-on-surface-variant font-bold uppercase tracking-tight">
                  Total de entregas pendientes:
                </p>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-[18px] font-bold text-primary leading-none">
                    {totalEntregas}
                  </span>
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
