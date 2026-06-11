import { useMonitor } from '../hooks/useMonitor'

interface MonitorPageProps {
  asignacionId: string
  materiaId: string
}

interface MetricCardProps {
  label: string
  value: number | string
}

function MetricCard({ label, value }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-surface-subtle bg-surface p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-text">{value}</p>
    </div>
  )
}

export function MonitorPage({ asignacionId, materiaId }: MonitorPageProps) {
  const { data, isLoading, isError, refetch } = useMonitor(asignacionId, materiaId)

  const sinContexto = !asignacionId || !materiaId

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Monitor de seguimiento</h1>

      {sinContexto && <p className="text-text-muted">No hay asignación seleccionada.</p>}
      {!sinContexto && isLoading && <p className="text-text-muted">Cargando datos del monitor...</p>}

      {!sinContexto && isError && (
        <div className="space-y-2">
          <p className="text-red-600">Error al cargar los datos del monitor.</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded-lg border border-surface-subtle px-4 py-2 text-sm font-medium text-text hover:bg-surface-subtle"
          >
            Reintentar
          </button>
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <MetricCard label="Total alumnos" value={data.total_alumnos} />
          <MetricCard label="Atrasados" value={data.atrasados} />
          <MetricCard label="Al día" value={data.al_dia} />
          <MetricCard
            label="Promedio general"
            value={data.promedio_general !== null ? data.promedio_general : '—'}
          />
          <MetricCard label="Comunicaciones enviadas" value={data.comunicaciones_enviadas} />
          <MetricCard label="Comunicaciones pendientes" value={data.comunicaciones_pendientes} />
        </div>
      )}
    </div>
  )
}
