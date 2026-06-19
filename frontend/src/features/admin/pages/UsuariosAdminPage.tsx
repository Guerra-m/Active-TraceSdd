import { Users, UserCheck, Activity, UserPlus, Edit, MoreVertical, UserX, Send, CheckCircle } from 'lucide-react'
import { RequirePermission } from '@/shared/components/RequirePermission'
import { Spinner } from '@/shared/components/Spinner'
import { useUsuariosAdmin, useUpdateUsuarioAdmin } from '../hooks/useUsuariosAdmin'
import type { UsuarioAdmin } from '../types'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getInitials(usuario: UsuarioAdmin): string {
  const nombre = usuario.nombre ?? ''
  const apellido = (usuario.apellidos ?? '').split(' ')[0] ?? ''
  return `${nombre.charAt(0)}${apellido.charAt(0)}`.toUpperCase() || '?'
}

function StatusBadge({ estado, isActive }: { estado: string; isActive: boolean }) {
  if (isActive) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-800 text-[11px] font-bold rounded-full border border-green-200">
        <span className="w-1.5 h-1.5 rounded-full bg-green-600" />
        {estado}
      </span>
    )
  }
  if (estado?.toLowerCase() === 'invitado') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 text-[11px] font-bold rounded-full border border-amber-200">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
        {estado}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] font-bold rounded-full border border-slate-200">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
      {estado}
    </span>
  )
}

// ─── Fila de Usuario ──────────────────────────────────────────────────────────

function UsuarioRow({
  usuario,
  onToggle,
}: {
  usuario: UsuarioAdmin
  onToggle: (id: string, nuevoEstado: string) => void
}) {
  const activo = usuario.is_active
  const initials = getInitials(usuario)

  return (
    <tr className="hover:bg-surface-subtle transition-colors group">
      <td className="px-3 py-4">
        <input className="rounded border-slate-300 text-brand-600 h-3.5 w-3.5" type="checkbox" />
      </td>
      <td className="px-3 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 font-bold text-sm flex-shrink-0">
            {initials}
          </div>
          <div>
            <p className="text-sm font-semibold text-text leading-tight">
              {usuario.nombre ?? '—'} {usuario.apellidos ?? ''}
            </p>
            <p className="font-mono text-xs text-text-muted">
              {usuario.legajo ? `Legajo: ${usuario.legajo}` : 'Sin legajo'}
            </p>
          </div>
        </div>
      </td>
      <td className="px-3 py-4">
        {usuario.facturador ? (
          <span className="px-2 py-0.5 bg-brand-100 text-brand-700 text-[11px] font-bold rounded uppercase tracking-wider">
            Facturador
          </span>
        ) : (
          <span className="px-2 py-0.5 bg-surface-subtle text-text-muted text-[11px] font-bold rounded uppercase tracking-wider">
            Usuario
          </span>
        )}
      </td>
      <td className="px-3 py-4">
        <StatusBadge estado={usuario.estado} isActive={activo} />
      </td>
      <td className="px-3 py-4 font-mono text-xs text-text-muted">—</td>
      <td className="px-3 py-4 text-right">
        <div className="flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {activo ? (
            <button
              onClick={() => onToggle(usuario.id, 'Inactivo')}
              className="w-8 h-8 flex items-center justify-center text-red-600 bg-red-50 hover:bg-red-100 rounded transition-colors"
              title="Desactivar usuario"
            >
              <UserX className="w-4 h-4" />
            </button>
          ) : usuario.estado?.toLowerCase() === 'invitado' ? (
            <button
              className="w-8 h-8 flex items-center justify-center text-brand-600 hover:bg-brand-50 rounded transition-colors"
              title="Reenviar invitación"
            >
              <Send className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => onToggle(usuario.id, 'Activo')}
              className="w-8 h-8 flex items-center justify-center text-green-700 hover:bg-green-50 rounded transition-colors"
              title="Activar usuario"
            >
              <CheckCircle className="w-4 h-4" />
            </button>
          )}
          <button className="w-8 h-8 flex items-center justify-center text-text-muted hover:bg-surface-subtle rounded transition-colors">
            <Edit className="w-4 h-4" />
          </button>
          <button className="w-8 h-8 flex items-center justify-center text-text-muted hover:bg-surface-subtle rounded transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
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

  const totalUsers = items.length
  const activeUsers = items.filter((u) => u.is_active).length
  const facturadores = items.filter((u) => u.facturador).length

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Error al cargar los usuarios. Intentá de nuevo.
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Breadcrumbs & Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-text-muted mb-1">
            <span>Dashboard</span>
            <span className="mx-0.5">›</span>
            <span className="text-text font-medium">Gestión de Usuarios</span>
          </nav>
          <h2 className="text-2xl font-bold tracking-tight text-text">Gestión de Usuarios</h2>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors shadow-sm">
          <UserPlus className="w-4 h-4" />
          Invitar Usuario
        </button>
      </div>

      {/* Stats Bento Grid */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-surface p-4 border border-surface-subtle rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <div className="p-2 bg-brand-50 rounded-lg">
              <Users className="w-5 h-5 text-brand-600" />
            </div>
            <span className="text-[11px] font-semibold text-green-600">Todos</span>
          </div>
          <p className="text-[11px] font-bold text-text-muted uppercase tracking-wider mb-1">TOTAL USUARIOS</p>
          <h3 className="text-2xl font-bold text-text">{totalUsers}</h3>
        </div>
        <div className="bg-surface p-4 border border-surface-subtle rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <UserCheck className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-[11px] font-semibold text-text-muted">Activos ahora</span>
          </div>
          <p className="text-[11px] font-bold text-text-muted uppercase tracking-wider mb-1">ACTIVOS</p>
          <h3 className="text-2xl font-bold text-text">{activeUsers}</h3>
        </div>
        <div className="bg-surface p-4 border border-surface-subtle rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <div className="p-2 bg-amber-50 rounded-lg">
              <Users className="w-5 h-5 text-amber-600" />
            </div>
            <span className="text-[11px] font-semibold text-text-muted">Rol especial</span>
          </div>
          <p className="text-[11px] font-bold text-text-muted uppercase tracking-wider mb-1">FACTURADORES</p>
          <h3 className="text-2xl font-bold text-text">{facturadores}</h3>
        </div>
        <div className="bg-surface p-4 border border-surface-subtle rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <div className="p-2 bg-surface-subtle rounded-lg">
              <Activity className="w-5 h-5 text-text-muted" />
            </div>
            <span className="text-[11px] font-semibold text-text-muted">Total</span>
          </div>
          <p className="text-[11px] font-bold text-text-muted uppercase tracking-wider mb-1">INACTIVOS</p>
          <h3 className="text-2xl font-bold text-text">{totalUsers - activeUsers}</h3>
        </div>
      </div>

      {/* Table Filters Bar */}
      <div className="bg-surface border border-surface-subtle rounded-t-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-muted rounded border border-surface-subtle cursor-pointer hover:bg-surface-subtle transition-colors text-sm font-medium text-text-muted">
            Rol: Todos los roles
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-muted rounded border border-surface-subtle cursor-pointer hover:bg-surface-subtle transition-colors text-sm font-medium text-text-muted">
            Estado: Todos
          </div>
        </div>
        <span className="text-sm text-text-muted">
          Mostrando {items.length} usuario{items.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* User Data Table */}
      {items.length === 0 ? (
        <div className="bg-surface border-x border-b border-surface-subtle rounded-b-xl p-8 text-center">
          <p className="text-sm text-text-muted">No hay usuarios registrados.</p>
        </div>
      ) : (
        <div className="bg-surface border-x border-b border-surface-subtle rounded-b-xl overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead className="bg-surface-muted sticky top-0 z-10 border-b border-surface-subtle">
              <tr>
                <th className="px-3 py-2 w-10">
                  <input className="rounded border-slate-300 text-brand-600 h-3.5 w-3.5" type="checkbox" />
                </th>
                <th className="px-3 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">
                  Nombre e Identidad
                </th>
                <th className="px-3 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">
                  Roles
                </th>
                <th className="px-3 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-3 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider">
                  Última Actividad
                </th>
                <th className="px-3 py-2 text-[11px] font-bold text-text-muted uppercase tracking-wider text-right">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-subtle">
              {items.map((u) => (
                <UsuarioRow key={u.id} usuario={u} onToggle={handleToggle} />
              ))}
            </tbody>
          </table>

          {/* Pagination Footer */}
          <div className="px-6 py-3 bg-surface border-t border-surface-subtle flex justify-between items-center">
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-muted">Filas por página:</span>
              <select className="bg-transparent border-none text-sm focus:ring-0 cursor-pointer text-text-muted">
                <option>10</option>
                <option>25</option>
                <option>50</option>
              </select>
            </div>
            <span className="text-sm text-text-muted">
              1 - {items.length} de {items.length}
            </span>
          </div>
        </div>
      )}

      {updateMutation.isError && (
        <p role="alert" className="text-sm text-red-600">
          Error al actualizar el usuario. Intentá de nuevo.
        </p>
      )}

      {/* Help Cards */}
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div className="flex gap-4 p-5 bg-brand-50 border border-brand-100 rounded-xl">
          <div className="flex-shrink-0 mt-0.5">
            <UserCheck className="w-5 h-5 text-brand-600" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-text mb-1">Seguridad en acciones sensibles</h4>
            <p className="text-xs text-text-muted">
              La función de <strong>Impersonación</strong> crea una traza de auditoría de alto nivel. Todas las acciones
              realizadas mientras se impersona un usuario quedan registradas con tu ID de admin y el del usuario objetivo.
            </p>
          </div>
        </div>
        <div className="flex gap-4 p-5 bg-surface border border-surface-subtle rounded-xl">
          <div className="flex-shrink-0 mt-0.5">
            <Edit className="w-5 h-5 text-text-muted" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-text mb-1">Gestión masiva</h4>
            <p className="text-xs text-text-muted">
              Seleccioná múltiples usuarios para realizar acciones masivas como asignación de roles, reseteo de contraseñas
              o desactivación de cuentas.
            </p>
          </div>
        </div>
      </div>
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
