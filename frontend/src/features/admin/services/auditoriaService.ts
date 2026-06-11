import { api } from '@/shared/services/api'
import type { AuditLog, AuditLogFiltros, AuditPanel, PagedResponse } from '../types'

export async function fetchAuditLogs(filtros?: AuditLogFiltros): Promise<PagedResponse<AuditLog>> {
  const { data } = await api.get<PagedResponse<AuditLog>>('/v1/auditoria/', { params: filtros })
  return data
}

export async function fetchAuditPanel(params?: {
  desde?: string
  hasta?: string
}): Promise<AuditPanel> {
  const { data } = await api.get<AuditPanel>('/v1/auditoria/panel', { params })
  return data
}
