import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useUsuariosAdmin, useUpdateUsuarioAdmin } from '../hooks/useUsuariosAdmin'
import type { UsuarioAdmin } from '../types'

// ─── Fila de Usuario ──────────────────────────────────────────────────────────

function UsuarioRow({
  usuario,
  onToggle,
}: {
  usuario: UsuarioAdmin
  onToggle: (id: string, nuevoEstado: string) => void
}) {
  const activo = usuario.is_active

  return (
    <tr className="border-b border-border">
      <td className="p-3 font-medium">
        {usuario.nombre ?? '—'} {usuario.apellidos ?? ''}
      </td>
      <td className="p-3 font-mono text-xs text-gray-500">{usuario.legajo ?? '—'}</td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${
            activo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {usuario.estado}
        </span>
      </td>
      <td className="p-3">
        {usuario.facturador && (
          <span className="rounded bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800">
            Facturador
          </span>
        )}
      </td>
      <td className="p-3">
        <button
          onClick={() => onToggle(usuario.id, activo ? 'Inactivo' : 'Activo')}
          className={`rounded border px-3 py-1 text-sm ${
            activo
              ? 'border-red-300 text-red-600 hover:bg-red-50'
              : 'border-green-300 text-green-600 hover:bg-green-50'
          }`}
        >
          {activo ? 'Desactivar' : 'Activar'}
        </button>
      </td>
    </tr>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

function UsuariosAdminContent() {
  const { data, isLoading, isError } = useUsuariosAdmin()
  const updateMutation = useUpdateUsuarioAdmin()
  const items = data ?? []

  const handleToggle = (id: string, nuevoEstado: string) => {
    updateMutation.mutate({ id, payload: { estado: nuevoEstado } })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded bg-red-50 p-4 text-red-700">
        Error al cargar los usuarios. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Usuarios del tenant</h1>

      {items.length === 0 ? (
        <p className="text-gray-500">No hay usuarios registrados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Nombre</th>
                <th className="p-3 text-left">Legajo</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((u) => (
                <UsuarioRow key={u.id} usuario={u} onToggle={handleToggle} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {updateMutation.isError && (
        <p role="alert" className="text-sm text-red-600">
          Error al actualizar el usuario. Intentá de nuevo.
        </p>
      )}
    </div>
  )
}

export function UsuariosAdminPage() {
  return (
    <RequirePermission permission="estructura:gestionar">
      <UsuariosAdminContent />
    </RequirePermission>
  )
}
