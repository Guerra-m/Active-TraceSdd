import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen overflow-hidden bg-surface-muted">
      <div
        className={`flex-shrink-0 overflow-hidden transition-all duration-200 ${
          sidebarOpen ? 'w-60' : 'w-0'
        }`}
      >
        <Sidebar />
      </div>
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Topbar onMenuClick={() => setSidebarOpen((o) => !o)} sidebarOpen={sidebarOpen} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
