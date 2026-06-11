import { useQuery } from '@tanstack/react-query'
import { fetchAuditLogs, fetchAuditPanel } from '../services/auditoriaService'
import type { AuditLogFiltros } from '../types'

export const AUDIT_LOGS_KEY = 'admin-audit-logs'
export const AUDIT_PANEL_KEY = 'admin-audit-panel'

export function useAuditLogs(filtros?: AuditLogFiltros) {
  return useQuery({
    queryKey: [AUDIT_LOGS_KEY, filtros],
    queryFn: () => fetchAuditLogs(filtros),
  })
}

export function useAuditPanel(params?: { desde?: string; hasta?: string }) {
  return useQuery({
    queryKey: [AUDIT_PANEL_KEY, params],
    queryFn: () => fetchAuditPanel(params),
  })
}
