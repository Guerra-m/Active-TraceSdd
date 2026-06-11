import { NavLink } from 'react-router-dom'
import { useAuth } from '@/features/auth/context/AuthContext'
import { MENU_ITEMS } from './menuConfig'

export function Sidebar() {
  const { permissions } = useAuth()

  const visibleItems = MENU_ITEMS.filter((item) => permissions.includes(item.permission))

  return (
    <aside className="flex h-full w-64 flex-col bg-surface border-r border-surface-subtle">
      <div className="flex h-16 items-center px-6 border-b border-surface-subtle">
        <span className="text-lg font-bold text-text">activia-trace</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Navegación principal">
        <ul className="space-y-1">
          {visibleItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-text-muted hover:bg-surface-subtle hover:text-text'
                  }`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
