import { Download, Mail, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAtrasados, useRanking, useNotasFinales } from '../hooks/useAtrasados'

function exportarCSV(rows: { apellidos: string; nombre: string; faltantes: string[]; reprobadas: string[] }[]) {
  const header = 'Apellido,Nombre,Actividades Faltantes,Estado'
  const body = rows.map(r =>
    `"${r.apellidos}","${r.nombre}","${r.faltantes.join('; ')}","${r.reprobadas.length > 0 ? 'Reprobadas' : 'Pendiente'}"`
  ).join('\n')
  const blob = new Blob([header + '\n' + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `atrasados_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

interface AtrasadosPageProps {
  asignacionId: string
  materiaId: string
}

// ─── Initials avatar ─────────────────────────────────────────────────────────

const AVATAR_COLORS = [
  'bg-primary-fixed text-primary',
  'bg-secondary-fixed text-secondary',
  'bg-tertiary-fixed text-tertiary',
  'bg-primary-fixed-dim text-primary',
  'bg-secondary-fixed-dim text-secondary',
  'bg-tertiary-fixed-dim text-tertiary',
]

function Avatar({ nombre, apellidos, index }: { nombre: string; apellidos: string; index: number }) {
  const initials = `${nombre.charAt(0)}${apellidos.charAt(0)}`.toUpperCase()
  const colorClass = AVATAR_COLORS[index % AVATAR_COLORS.length]
  return (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${colorClass}`}
    >
      {initials}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function AtrasadosPage({ asignacionId, materiaId }: AtrasadosPageProps) {
  const navigate = useNavigate()
  const { data: resp, isLoading: loadingAtrasados, isError: errorAtrasados } = useAtrasados(asignacionId, materiaId)
  const { data: rankingResp } = useRanking(asignacionId, materiaId)
  const { data: notasResp } = useNotasFinales(asignacionId, materiaId)

  const sinContexto = !asignacionId || !materiaId
  const atrasados = resp?.alumnos ?? []
  const ranking = rankingResp?.ranking ?? []
  void notasResp

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <nav className="flex items-center gap-1 mb-2 text-[13px] text-on-surface-variant">
            <span>Dashboard</span>
            <span className="text-outline mx-1">/</span>
            <span className="font-semibold text-primary">Alumnos atrasados</span>
          </nav>
          <h2 className="text-[30px] leading-[38px] tracking-tight font-semibold text-on-background">
            Resumen administrativo
          </h2>
          <p className="text-[14px] text-on-surface-variant mt-1">
            Identificá y comunicate con los alumnos que superaron los plazos de entrega.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportarCSV(atrasados)}
            disabled={atrasados.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-[14px] font-medium hover:bg-surface-container-low transition-colors disabled:opacity-50"
          >
            <Download className="h-5 w-5" />
            Exportar reporte
          </button>
          <button
            onClick={() => navigate('/profesor/comunicaciones')}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg text-[14px] font-medium hover:opacity-90 transition-all"
          >
            <Mail className="h-5 w-5" />
            Recordatorio masivo
          </button>
        </div>
      </div>

      {sinContexto && (
        <p className="text-[14px] text-on-surface-variant">No hay asignación seleccionada.</p>
      )}

      {!sinContexto && (
        <>
          {/* Tabla de atrasados */}
          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center">
              <h3 className="text-[16px] leading-6 font-medium text-primary">
                Lista de entregas atrasadas
              </h3>
              {atrasados.length > 0 && (
                <span className="text-[13px] text-on-surface-variant">
                  {atrasados.length} alumno{atrasados.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {loadingAtrasados && (
              <p className="px-6 py-6 text-[14px] text-on-surface-variant">Cargando...</p>
            )}
            {errorAtrasados && (
              <p className="px-6 py-6 text-[14px] text-error">Error al cargar los datos.</p>
            )}
            {!loadingAtrasados && !errorAtrasados && atrasados.length === 0 && (
              <p className="px-6 py-6 text-[14px] text-on-surface-variant">
                No hay alumnos atrasados en esta comisión.
              </p>
            )}

            {atrasados.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low border-b border-outline-variant">
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">
                        Alumno
                      </th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">
                        Faltantes
                      </th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline text-right">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {atrasados.map((a, i) => (
                      <tr key={a.entrada_padron_id} className="hover:bg-surface-container-high transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Avatar nombre={a.nombre} apellidos={a.apellidos} index={i} />
                            <span className="text-[14px] font-medium text-on-surface">
                              {a.apellidos}, {a.nombre}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-mono text-[12px] font-bold text-error">
                            {a.faltantes.length > 0 ? a.faltantes.join(', ') : '—'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {a.reprobadas.length > 0 ? (
                            <span className="px-2 py-1 bg-error-container text-on-error-container rounded text-[11px] font-bold uppercase tracking-tight">
                              Reprobadas
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-surface-container-high text-on-surface-variant rounded text-[11px] font-bold uppercase tracking-tight">
                              Pendiente
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => navigate('/profesor/comunicaciones')}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-container text-on-primary-container rounded-lg text-[13px] font-medium hover:opacity-80 transition-all"
                          >
                            <Mail className="h-4 w-4" />
                            Recordatorio
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Tarjetas de resumen — visibles cuando hay datos */}
          {(rankingResp || notasResp) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Promedio de atraso */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <AlertTriangle className="h-5 w-5 text-primary" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Alumnos atrasados</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[30px] leading-[38px] font-semibold">{atrasados.length}</span>
                  <span className="text-[13px] text-on-surface-variant">en esta comisión</span>
                </div>
              </div>

              {/* Ranking top */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <TrendingUp className="h-5 w-5 text-secondary" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Mejor posición</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[30px] leading-[38px] font-semibold">
                    {ranking.length > 0 ? ranking[0].aprobadas : '—'}
                  </span>
                  <span className="text-[13px] text-on-surface-variant">aprobadas (1°)</span>
                </div>
                {ranking.length > 0 && (
                  <div className="mt-2 text-[11px] text-on-secondary-container font-medium flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5" />
                    {ranking[0].apellidos}, {ranking[0].nombre}
                  </div>
                )}
              </div>

              {/* Salud de entregas */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-sm relative overflow-hidden">
                <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
                  <CheckCircle className="h-5 w-5 text-tertiary" />
                  <span className="text-[11px] font-bold uppercase tracking-widest">Salud de entregas</span>
                </div>
                {notasResp && notasResp.alumnos.length > 0 ? (
                  <>
                    <div className="flex items-baseline gap-1">
                      <span className="text-[30px] leading-[38px] font-semibold">
                        {Math.round(
                          (notasResp.alumnos.filter((n) => n.promedio_numerico !== null && n.promedio_numerico >= 4).length /
                            notasResp.alumnos.length) *
                            100
                        )}%
                      </span>
                      <span className="text-[13px] text-on-surface-variant">aprobando</span>
                    </div>
                    <div className="mt-2 w-full h-1 bg-surface-container rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${Math.round(
                            (notasResp.alumnos.filter((n) => n.promedio_numerico !== null && n.promedio_numerico >= 4).length /
                              notasResp.alumnos.length) *
                              100
                          )}%`,
                        }}
                      />
                    </div>
                  </>
                ) : (
                  <span className="text-[30px] leading-[38px] font-semibold">—</span>
                )}
              </div>
            </div>
          )}

          {/* Tabla ranking */}
          {ranking.length > 0 && (
            <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-outline-variant">
                <h3 className="text-[16px] leading-6 font-medium text-primary">Ranking</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low border-b border-outline-variant">
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">#</th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Alumno</th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Aprobadas</th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {ranking.map((r, i) => (
                      <tr key={r.entrada_padron_id} className="hover:bg-surface-container-high transition-colors">
                        <td className="px-6 py-4 font-mono text-[12px] text-secondary">{r.posicion}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Avatar nombre={r.nombre} apellidos={r.apellidos} index={i} />
                            <span className="text-[14px] font-medium text-on-surface">
                              {r.apellidos}, {r.nombre}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-[14px] text-on-surface">{r.aprobadas}</td>
                        <td className="px-6 py-4 text-[14px] text-on-surface">{r.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {rankingResp && ranking.length === 0 && (
            <p className="text-[14px] text-on-surface-variant">No hay datos de ranking aún.</p>
          )}

          {/* Tabla notas finales */}
          {notasResp && notasResp.alumnos.length > 0 && (
            <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-outline-variant">
                <h3 className="text-[16px] leading-6 font-medium text-primary">Notas finales</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low border-b border-outline-variant">
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Alumno</th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Promedio</th>
                      <th className="px-6 py-3 text-[11px] font-bold uppercase tracking-widest text-outline">Aprobadas / Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {notasResp.alumnos.map((n, i) => (
                      <tr key={n.entrada_padron_id} className="hover:bg-surface-container-high transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Avatar nombre={n.nombre} apellidos={n.apellidos} index={i} />
                            <span className="text-[14px] font-medium text-on-surface">
                              {n.apellidos}, {n.nombre}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 font-mono text-[12px] font-bold text-primary">
                          {n.promedio_numerico !== null ? n.promedio_numerico : '—'}
                        </td>
                        <td className="px-6 py-4 text-[14px] text-on-surface">
                          {n.aprobadas} / {n.total}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {notasResp && notasResp.alumnos.length === 0 && (
            <p className="text-[14px] text-on-surface-variant">No hay calificaciones registradas.</p>
          )}
        </>
      )}
    </div>
  )
}
