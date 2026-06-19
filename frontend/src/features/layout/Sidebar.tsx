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
    <aside className="flex h-full w-60 flex-col bg-surface border-r border-outline-variant">
      {/* Logo / Brand */}
      <div className="flex items-center gap-2 px-2 py-4 mb-8">
        <div className="w-10 h-10 bg-primary rounded flex items-center justify-center text-on-primary shrink-0">
          <LayoutDashboard className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-[20px] leading-7 font-semibold text-primary leading-tight tracking-tight">
            Activia-Trace
          </h1>
          <p className="text-[13px] leading-[18px] text-on-surface-variant opacity-70">
            Academic Management
          </p>
        </div>
      </div>

      <nav
        className="flex-1 overflow-y-auto px-2 space-y-1"
        aria-label="Navegación principal"
      >
        {/* Dashboard — direct link */}
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center gap-4 p-2 rounded-lg text-[14px] leading-5 font-medium transition-colors ${
              isActive
                ? 'bg-secondary-container text-on-secondary-container'
                : 'text-on-surface-variant hover:bg-surface-container-low'
            }`
          }
        >
          <LayoutDashboard className="h-[22px] w-[22px] shrink-0" />
          <span>Dashboard</span>
        </NavLink>

        {/* Collapsible sections */}
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
                className="flex w-full items-center justify-between p-2 rounded-lg text-[14px] leading-5 text-on-surface-variant hover:bg-surface-container-low transition-colors"
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-4">
                  <Icon className="h-[22px] w-[22px] shrink-0" />
                  <span>{section.label}</span>
                </div>
                <ChevronRight
                  className={`h-4 w-4 shrink-0 transition-transform duration-200 ${
                    isOpen ? 'rotate-90' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <ul className="mt-0.5 mb-1 space-y-0.5 pl-10 pr-1">
                  {visibleItems.map((item) => (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        className={({ isActive }) =>
                          `block rounded-lg px-3 py-2 text-[14px] leading-5 transition-colors ${
                            isActive
                              ? 'bg-secondary-container text-on-secondary-container font-medium'
                              : 'text-on-surface-variant hover:bg-surface-container-low'
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
