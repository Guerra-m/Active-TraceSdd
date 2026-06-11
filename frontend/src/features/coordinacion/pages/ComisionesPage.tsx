import { useQuery } from '@tanstack/react-query'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { api } from '@/shared/services/api'

interface Asignacion {
  id: string
  tenant_id: string
  usuario_id: string
  rol: string
  materia_id: string | null
  carrera_id: string | null
  cohorte_id: string | null
  comisiones: string[]
  responsable_id: string | null
  desde: string
  hasta: string | null
  estado_vigencia: string
}

function fetchAsignaciones(): Promise<Asignacion[]> {
  return api.get<Asignacion[]>('/asignaciones').then((r) => r.data)
}

function VigenciaBadge({ estado }: { estado: string }) {
  const cls =
    estado === 'Vigente'
      ? 'bg-green-100 text-green-800'
      : estado === 'Pendiente'
        ? 'bg-yellow-100 text-yellow-800'
        : 'bg-gray-100 text-gray-600'
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{estado}</span>
  )
}

function AsignacionRow({ a }: { a: Asignacion }) {
  return (
    <tr className="border-b border-border hover:bg-surface-subtle">
      <td className="p-3 font-mono text-xs text-gray-500">{a.usuario_id.slice(0, 8)}</td>
      <td className="p-3 text-sm font-medium">{a.rol}</td>
      <td className="p-3 text-sm text-gray-600">
        {a.comisiones.length > 0 ? a.comisiones.join(', ') : <span className="text-gray-400">—</span>}
      </td>
      <td className="p-3 text-xs text-gray-500">
        {a.materia_id ? a.materia_id.slice(0, 8) : '—'}
      </td>
      <td className="p-3 text-xs text-gray-500">
        {a.desde.slice(0, 10)}
        {a.hasta ? ` → ${a.hasta.slice(0, 10)}` : ''}
      </td>
      <td className="p-3">
        <VigenciaBadge estado={a.estado_vigencia} />
      </td>
    </tr>
  )
}

function ComisionesContent() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['asignaciones'],
    queryFn: fetchAsignaciones,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <p role="alert" className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Error al cargar las comisiones.
      </p>
    )
  }

  const items = data ?? []
  const conComisiones = items.filter((a) => a.comisiones.length > 0)
  const sinComisiones = items.filter((a) => a.comisiones.length === 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Comisiones</h1>
        <span className="text-sm text-gray-500">{items.length} asignaciones totales</span>
      </div>

      {conComisiones.length > 0 && (
        <div>
          <h2 className="mb-2 text-base font-semibold">Con comisiones asignadas</h2>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-surface-subtle">
                <tr>
                  <th className="p-3 text-left font-medium text-gray-600">Usuario</th>
                  <th className="p-3 text-left font-medium text-gray-600">Rol</th>
                  <th className="p-3 text-left font-medium text-gray-600">Comisiones</th>
                  <th className="p-3 text-left font-medium text-gray-600">Materia</th>
                  <th className="p-3 text-left font-medium text-gray-600">Vigencia</th>
                  <th className="p-3 text-left font-medium text-gray-600">Estado</th>
                </tr>
              </thead>
              <tbody>
                {conComisiones.map((a) => (
                  <AsignacionRow key={a.id} a={a} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sinComisiones.length > 0 && (
        <div>
          <h2 className="mb-2 text-base font-semibold text-gray-500">Sin comisión específica</h2>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-surface-subtle">
                <tr>
                  <th className="p-3 text-left font-medium text-gray-600">Usuario</th>
                  <th className="p-3 text-left font-medium text-gray-600">Rol</th>
                  <th className="p-3 text-left font-medium text-gray-600">Comisiones</th>
                  <th className="p-3 text-left font-medium text-gray-600">Materia</th>
                  <th className="p-3 text-left font-medium text-gray-600">Vigencia</th>
                  <th className="p-3 text-left font-medium text-gray-600">Estado</th>
                </tr>
              </thead>
              <tbody>
                {sinComisiones.map((a) => (
                  <AsignacionRow key={a.id} a={a} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {items.length === 0 && (
        <p className="py-8 text-center text-gray-500">No hay asignaciones registradas.</p>
      )}
    </div>
  )
}

export function ComisionesPage() {
  return (
    <RequirePermission permission="equipos:asignar">
      <div className="p-6">
        <ComisionesContent />
      </div>
    </RequirePermission>
  )
}
