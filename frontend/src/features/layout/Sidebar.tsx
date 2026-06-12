import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ChevronRight, LayoutDashboard } from 'lucide-react'
import { useAuth } from '@/features/auth/context/AuthContext'
import { MENU_SECTIONS } from './menuConfig'

export function Sidebar() {
  const { permissions } = useAuth()
  const { pathname } = useLocation()

  const [openSections, setOpenSections] = useState<Set<string>>(() => {
    const initial = new Set<string>()
    for (const section of MENU_SECTIONS) {
      if (section.items.some((item) => pathname.startsWith(item.path))) {
        initial.add(section.id)
      }
    }
    return initial
  })

  useEffect(() => {
    for (const section of MENU_SECTIONS) {
      if (section.items.some((item) => pathname.startsWith(item.path))) {
        setOpenSections((prev) => new Set([...prev, section.id]))
        break
      }
    }
  }, [pathname])

  const toggleSection = (id: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <aside className="flex h-full w-60 flex-col bg-surface border-r border-surface-subtle">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-5 border-b border-surface-subtle">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-600">
          <span className="text-[11px] font-bold text-white tracking-tight">AT</span>
        </div>
        <span className="text-sm font-semibold text-text tracking-tight">activia-trace</span>
      </div>

      <nav
        className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5"
        aria-label="Navegación principal"
      >
        {/* Dashboard — acceso directo */}
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? 'bg-brand-50 text-brand-700'
                : 'text-text-muted hover:bg-surface-subtle hover:text-text'
            }`
          }
        >
          <LayoutDashboard className="h-4 w-4 shrink-0" />
          Dashboard
        </NavLink>

        {/* Separador */}
        <div className="my-2 border-t border-surface-subtle" />

        {/* Secciones colapsables */}
        {MENU_SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) =>
            permissions.includes(item.permission),
          )
          if (visibleItems.length === 0) return null

          const isOpen = openSections.has(section.id)
          const Icon = section.icon

          return (
            <div key={section.id}>
              <button
                onClick={() => toggleSection(section.id)}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm font-medium text-text-muted hover:bg-surface-subtle hover:text-text transition-colors"
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{section.label}</span>
                </div>
                <ChevronRight
                  className={`h-3.5 w-3.5 shrink-0 transition-transform duration-200 ${
                    isOpen ? 'rotate-90' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <ul className="mt-0.5 mb-1 space-y-0.5 pl-9 pr-1">
                  {visibleItems.map((item) => (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        className={({ isActive }) =>
                          `block rounded-md px-3 py-1.5 text-sm transition-colors ${
                            isActive
                              ? 'bg-brand-50 text-brand-700 font-medium'
                              : 'text-text-muted hover:bg-surface-subtle hover:text-text'
                          }`
                        }
                      >
                        {item.label}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
