import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useUsuariosAdmin, useUpdateUsuarioAdmin } from '../hooks/useUsuariosAdmin'
import type { UsuarioAdmin } from '../types'

// ─── Fila de Usuario ──────────────────────────────────────────────────────────

function UsuarioRow({
  usuario,
  onToggleActivo,
}: {
  usuario: UsuarioAdmin
  onToggleActivo: (id: string, activo: boolean) => void
}) {
  return (
    <tr className="border-b border-border">
      <td className="p-3 font-medium">{usuario.nombre}</td>
      <td className="p-3 text-gray-600">{usuario.email}</td>
      <td className="p-3">
        <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
          {usuario.rol}
        </span>
      </td>
      <td className="p-3">
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${
            usuario.activo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {usuario.activo ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td className="p-3">
        <button
          onClick={() => onToggleActivo(usuario.id, !usuario.activo)}
          className={`rounded border px-3 py-1 text-sm ${
            usuario.activo
              ? 'border-red-300 text-red-600 hover:bg-red-50'
              : 'border-green-300 text-green-600 hover:bg-green-50'
          }`}
        >
          {usuario.activo ? 'Desactivar' : 'Activar'}
        </button>
      </td>
    </tr>
  )
}

// ─── Content ──────────────────────────────────────────────────────────────────

function UsuariosAdminContent() {
  const { data, isLoading, isError } = useUsuariosAdmin()
  const updateMutation = useUpdateUsuarioAdmin()

  const handleToggleActivo = (id: string, activo: boolean) => {
    updateMutation.mutate({ id, payload: { activo } })
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

      {data?.items.length === 0 ? (
        <p className="text-gray-500">No hay usuarios registrados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">Nombre</th>
                <th className="p-3 text-left">Email</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Estado</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((u) => (
                <UsuarioRow key={u.id} usuario={u} onToggleActivo={handleToggleActivo} />
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
