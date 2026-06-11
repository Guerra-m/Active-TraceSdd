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

export function EntregasPage({ asignacionId, materiaId }: EntregasPageProps) {
  const { data: resp, isLoading, isError } = useEntregasSinCorregir(asignacionId, materiaId)

  const sinContexto = !asignacionId || !materiaId
  const entregas = resp?.items ?? []
  const sinEntregas = entregas.length === 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text">Entregas sin corregir</h1>
        <button
          type="button"
          disabled={sinEntregas}
          onClick={() => exportarCSV(entregas)}
          className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle disabled:cursor-not-allowed disabled:opacity-40"
        >
          Exportar CSV
        </button>
      </div>

      {sinContexto && <p className="text-text-muted">No hay asignación seleccionada.</p>}
      {!sinContexto && isLoading && <p className="text-text-muted">Cargando entregas...</p>}
      {!sinContexto && isError && <p className="text-red-600">Error al cargar las entregas.</p>}

      {!sinContexto && !isLoading && !isError && sinEntregas && (
        <p className="text-text-muted">No hay entregas pendientes de corrección</p>
      )}

      {entregas.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-surface-subtle">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Nombre</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Apellidos</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Actividad</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Importado el</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-subtle">
              {entregas.map((e, i) => (
                <tr key={`${e.entrada_padron_id}-${e.actividad}-${i}`} className="hover:bg-surface-subtle">
                  <td className="px-4 py-2 text-text">{e.nombre}</td>
                  <td className="px-4 py-2 text-text">{e.apellidos}</td>
                  <td className="px-4 py-2 text-text">{e.actividad}</td>
                  <td className="px-4 py-2 text-text">
                    {new Date(e.importado_at).toLocaleDateString('es-AR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
