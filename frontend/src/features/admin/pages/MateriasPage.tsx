import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useMaterias } from '../hooks/useEstructura'
import type { Materia } from '../types'

function EstadoBadge({ activa }: { activa: boolean }) {
  return (
    <span
      className={`rounded px-2 py-0.5 text-xs font-medium ${
        activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
      }`}
    >
      {activa ? 'Activa' : 'Inactiva'}
    </span>
  )
}

function MateriaRow({ materia }: { materia: Materia }) {
  return (
    <tr className="border-b border-border hover:bg-surface-subtle">
      <td className="p-3 font-mono text-xs text-gray-500">{materia.codigo}</td>
      <td className="p-3 font-medium">{materia.nombre}</td>
      <td className="p-3 text-sm text-gray-600">{materia.carrera_nombre ?? '—'}</td>
      <td className="p-3 text-sm text-gray-500">{materia.grupo_plus ?? '—'}</td>
      <td className="p-3">
        <EstadoBadge activa={materia.activa} />
      </td>
    </tr>
  )
}

function MateriasContent() {
  const { data, isLoading, isError } = useMaterias()

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
        Error al cargar las materias.
      </p>
    )
  }

  const items = data ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Materias</h1>
        <span className="text-sm text-gray-500">{items.length} materias</span>
      </div>

      {items.length === 0 ? (
        <p className="py-8 text-center text-gray-500">No hay materias registradas.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface-subtle">
              <tr>
                <th className="p-3 text-left font-medium text-gray-600">Código</th>
                <th className="p-3 text-left font-medium text-gray-600">Nombre</th>
                <th className="p-3 text-left font-medium text-gray-600">Carrera</th>
                <th className="p-3 text-left font-medium text-gray-600">Grupo plus</th>
                <th className="p-3 text-left font-medium text-gray-600">Estado</th>
              </tr>
            </thead>
            <tbody>
              {items.map((m) => (
                <MateriaRow key={m.id} materia={m} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-gray-400">
        Para crear o editar materias, usá{' '}
        <a href="/admin/estructura" className="text-blue-600 underline">
          Estructura académica
        </a>
        .
      </p>
    </div>
  )
}

export function MateriasPage() {
  return (
    <RequirePermission permission="estructura:gestionar">
      <div className="p-6">
        <MateriasContent />
      </div>
    </RequirePermission>
  )
}
