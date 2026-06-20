import { Menu, PanelLeftClose, Bell, History, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/context/AuthContext'

interface TopbarProps {
  onMenuClick: () => void
  sidebarOpen: boolean
}

export function Topbar({ onMenuClick, sidebarOpen }: TopbarProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="h-16 border-b border-outline-variant bg-surface-container-lowest flex justify-between items-center px-6 shrink-0 z-40">
      {/* Left: hamburger + search */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          aria-label={sidebarOpen ? 'Cerrar sidebar' : 'Abrir sidebar'}
          className="hover:bg-surface-container rounded-full p-2 text-on-surface-variant transition-colors focus:outline-none"
        >
          {sidebarOpen ? <PanelLeftClose className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>

        <div className="flex items-center gap-2 bg-surface-container-low rounded-full px-4 py-1.5 w-80">
          <svg className="w-4 h-4 text-outline shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            type="text"
            placeholder="Buscar alumnos, docentes o auditorías..."
            className="bg-transparent border-none focus:ring-0 text-[13px] leading-[18px] text-on-surface w-full outline-none placeholder:text-outline"
          />
        </div>
      </div>

      {/* Right: icon actions + user */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/avisos')}
          aria-label="Notificaciones"
          className="hover:bg-surface-container rounded-full p-2 text-on-surface-variant transition-colors active:scale-95"
        >
          <Bell className="h-5 w-5" />
        </button>
        <button
          onClick={() => navigate('/admin/auditoria')}
          aria-label="Historial de auditoría"
          className="hover:bg-surface-container rounded-full p-2 text-on-surface-variant transition-colors active:scale-95"
        >
          <History className="h-5 w-5" />
        </button>

        {/* Divider */}
        <div className="h-8 w-px bg-outline-variant mx-1" />

        {/* User info */}
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-[16px] leading-6 font-medium text-primary" data-testid="user-name">
              {user.nombre}
            </span>
            <div className="w-8 h-8 rounded-full bg-primary-fixed flex items-center justify-center text-on-primary-fixed text-xs font-bold shrink-0">
              {user.nombre
                .split(' ')
                .slice(0, 2)
                .map((n) => n[0])
                .join('')
                .toUpperCase()}
            </div>
          </div>
        )}

        <button
          onClick={() => void logout()}
          aria-label="Cerrar sesión"
          className="hover:bg-surface-container rounded-full p-2 text-on-surface-variant transition-colors focus:outline-none"
          title="Cerrar sesión"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
