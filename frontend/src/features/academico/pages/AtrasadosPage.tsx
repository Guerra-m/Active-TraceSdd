import { useAtrasados, useRanking, useNotasFinales } from '../hooks/useAtrasados'

interface AtrasadosPageProps {
  asignacionId: string
  materiaId: string
}

export function AtrasadosPage({ asignacionId, materiaId }: AtrasadosPageProps) {
  const { data: resp, isLoading: loadingAtrasados, isError: errorAtrasados } = useAtrasados(asignacionId, materiaId)
  const { data: rankingResp } = useRanking(asignacionId, materiaId)
  const { data: notasResp } = useNotasFinales(asignacionId, materiaId)

  const sinContexto = !asignacionId || !materiaId

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-text">Alumnos atrasados</h1>

      {sinContexto && (
        <p className="text-text-muted">No hay asignación seleccionada.</p>
      )}

      {/* Sección atrasados */}
      {!sinContexto && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-text">Atrasados</h2>
          {loadingAtrasados && <p className="text-text-muted">Cargando...</p>}
          {errorAtrasados && <p className="text-error">Error al cargar los datos.</p>}
          {resp && resp.alumnos.length === 0 && (
            <p className="text-text-muted">No hay alumnos atrasados en esta comisión</p>
          )}
          {resp && resp.alumnos.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-surface-subtle">
              <table className="w-full text-sm">
                <thead className="bg-surface-muted">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Apellidos</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Faltantes</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Reprobadas</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle">
                  {resp.alumnos.map((a) => (
                    <tr key={a.entrada_padron_id} className="hover:bg-surface-subtle">
                      <td className="px-4 py-2 text-text">{a.nombre}</td>
                      <td className="px-4 py-2 text-text">{a.apellidos}</td>
                      <td className="px-4 py-2 text-text">{a.faltantes.join(', ') || '—'}</td>
                      <td className="px-4 py-2 text-text">{a.reprobadas.join(', ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* Sección ranking */}
      {!sinContexto && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-text">Ranking</h2>
          {rankingResp && rankingResp.ranking.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-surface-subtle">
              <table className="w-full text-sm">
                <thead className="bg-surface-muted">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">#</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Apellidos</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Aprobadas</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle">
                  {rankingResp.ranking.map((r) => (
                    <tr key={r.entrada_padron_id} className="hover:bg-surface-subtle">
                      <td className="px-4 py-2 text-text">{r.posicion}</td>
                      <td className="px-4 py-2 text-text">{r.nombre}</td>
                      <td className="px-4 py-2 text-text">{r.apellidos}</td>
                      <td className="px-4 py-2 text-text">{r.aprobadas}</td>
                      <td className="px-4 py-2 text-text">{r.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            rankingResp && <p className="text-text-muted">No hay datos de ranking aún.</p>
          )}
        </section>
      )}

      {/* Sección notas finales */}
      {!sinContexto && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-text">Notas finales</h2>
          {notasResp && notasResp.alumnos.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-surface-subtle">
              <table className="w-full text-sm">
                <thead className="bg-surface-muted">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Apellidos</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Promedio</th>
                    <th className="px-4 py-2 text-left font-medium text-text-muted">Aprobadas / Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-subtle">
                  {notasResp.alumnos.map((n) => (
                    <tr key={n.entrada_padron_id} className="hover:bg-surface-subtle">
                      <td className="px-4 py-2 text-text">{n.nombre}</td>
                      <td className="px-4 py-2 text-text">{n.apellidos}</td>
                      <td className="px-4 py-2 text-text">
                        {n.promedio_numerico !== null ? n.promedio_numerico : '—'}
                      </td>
                      <td className="px-4 py-2 text-text">{n.aprobadas} / {n.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            notasResp && <p className="text-text-muted">No hay calificaciones registradas.</p>
          )}
        </section>
      )}
    </div>
  )
}
