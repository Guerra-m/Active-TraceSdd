import { useAtrasados, useRanking, useNotasFinales } from '../hooks/useAtrasados'

interface AtrasadosPageProps {
  comisionId: string
}

export function AtrasadosPage({ comisionId }: AtrasadosPageProps) {
  const { data: atrasados, isLoading: loadingAtrasados, isError: errorAtrasados } = useAtrasados(comisionId)
  const { data: ranking } = useRanking(comisionId)
  const { data: notas } = useNotasFinales(comisionId)

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-text">Alumnos atrasados</h1>

      {/* Sección atrasados */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-text">Atrasados</h2>
        {loadingAtrasados && <p className="text-text-muted">Cargando...</p>}
        {errorAtrasados && (
          <p className="text-error">Error al cargar los datos.</p>
        )}
        {atrasados && atrasados.length === 0 && (
          <p className="text-text-muted">No hay alumnos atrasados en esta comisión</p>
        )}
        {atrasados && atrasados.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-subtle">
            <table className="w-full text-sm">
              <thead className="bg-surface-muted">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Legajo</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Entregas atrasadas</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Último atraso</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-subtle">
                {atrasados.map((a) => (
                  <tr key={a.id} className="hover:bg-surface-subtle">
                    <td className="px-4 py-2 text-text">{a.nombre}</td>
                    <td className="px-4 py-2 text-text">{a.legajo}</td>
                    <td className="px-4 py-2 text-text">{a.entregas_atrasadas}</td>
                    <td className="px-4 py-2 text-text">{a.ultimo_atraso}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Sección ranking */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-text">Ranking</h2>
        {ranking && ranking.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-surface-subtle">
            <table className="w-full text-sm">
              <thead className="bg-surface-muted">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">#</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Legajo</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Promedio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-subtle">
                {ranking.map((r) => (
                  <tr key={r.legajo} className="hover:bg-surface-subtle">
                    <td className="px-4 py-2 text-text">{r.posicion}</td>
                    <td className="px-4 py-2 text-text">{r.nombre}</td>
                    <td className="px-4 py-2 text-text">{r.legajo}</td>
                    <td className="px-4 py-2 text-text">{r.promedio}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !ranking && <p className="text-text-muted">Cargando ranking...</p>
        )}
      </section>

      {/* Sección notas finales */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-text">Notas finales</h2>
        {notas && notas.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-surface-subtle">
            <table className="w-full text-sm">
              <thead className="bg-surface-muted">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Legajo</th>
                  <th className="px-4 py-2 text-left font-medium text-text-muted">Nota final</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-subtle">
                {notas.map((n) => (
                  <tr key={n.id} className="hover:bg-surface-subtle">
                    <td className="px-4 py-2 text-text">{n.nombre}</td>
                    <td className="px-4 py-2 text-text">{n.legajo}</td>
                    <td className="px-4 py-2 text-text">
                      {n.nota_final !== null ? n.nota_final : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !notas && <p className="text-text-muted">Cargando notas...</p>
        )}
      </section>
    </div>
  )
}
