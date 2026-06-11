import { useAuth } from '@/features/auth/context/AuthContext'

export function Topbar() {
  const { user, logout } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-subtle bg-surface px-6">
      <div />

      <div className="flex items-center gap-4">
        {user && (
          <div className="text-right">
            <p className="text-sm font-medium text-text" data-testid="user-name">
              {user.nombre}
            </p>
            <p className="text-xs text-text-muted capitalize">{user.rol.toLowerCase()}</p>
          </div>
        )}

        <button
          onClick={() => void logout()}
          className="rounded-lg border border-surface-subtle px-3 py-1.5 text-sm text-text-muted hover:border-brand-300 hover:text-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}
