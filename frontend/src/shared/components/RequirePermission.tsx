import { ReactNode } from 'react'
import { useAuth } from '@/features/auth/context/AuthContext'

interface RequirePermissionProps {
  permission: string
  children: ReactNode
  fallback?: ReactNode
}

export function RequirePermission({ permission, children, fallback }: RequirePermissionProps) {
  const { permissions } = useAuth()

  if (!permissions.includes(permission)) {
    return <>{fallback ?? <div className="text-text-muted p-4">No tenés permiso para ver este contenido.</div>}</>
  }

  return <>{children}</>
}
