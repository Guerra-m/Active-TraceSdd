import { useEntregasSinCorregir } from '../hooks/useEntregas'
import type { EntregaSinCorregir } from '../types'

interface EntregasPageProps {
  comisionId: string
}

function exportarCSV(entregas: EntregaSinCorregir[]) {
  const headers = ['Alumno', 'Legajo', 'Actividad', 'Fecha de entrega', 'Estado']
  const rows = entregas.map((e) => [
    e.alumno_nombre,
    e.alumno_legajo,
    e.actividad,
    e.fecha_entrega,
    e.estado,
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

export function EntregasPage({ comisionId }: EntregasPageProps) {
  const { data: entregas, isLoading, isError } = useEntregasSinCorregir(comisionId)

  const sinEntregas = !entregas || entregas.length === 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text">Entregas sin corregir</h1>
        <button
          type="button"
          disabled={sinEntregas}
          onClick={() => entregas && exportarCSV(entregas)}
          className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle disabled:cursor-not-allowed disabled:opacity-40"
        >
          Exportar CSV
        </button>
      </div>

      {isLoading && <p className="text-text-muted">Cargando entregas...</p>}

      {isError && <p className="text-red-600">Error al cargar las entregas.</p>}

      {entregas && entregas.length === 0 && (
        <p className="text-text-muted">No hay entregas pendientes de corrección</p>
      )}

      {entregas && entregas.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-surface-subtle">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Alumno</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Legajo</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Actividad</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Fecha de entrega</th>
                <th className="px-4 py-2 text-left font-medium text-text-muted">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-subtle">
              {entregas.map((e) => (
                <tr key={e.id} className="hover:bg-surface-subtle">
                  <td className="px-4 py-2 text-text">{e.alumno_nombre}</td>
                  <td className="px-4 py-2 text-text">{e.alumno_legajo}</td>
                  <td className="px-4 py-2 text-text">{e.actividad}</td>
                  <td className="px-4 py-2 text-text">{e.fecha_entrega}</td>
                  <td className="px-4 py-2 text-text">{e.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
