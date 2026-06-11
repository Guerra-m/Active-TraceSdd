import { api } from '@/shared/services/api'
import type { AuditLog, AuditLogFiltros, MetricasAuditoria } from '../types'

export async function fetchAuditLogs(filtros?: AuditLogFiltros): Promise<AuditLog[]> {
  const { data } = await api.get<AuditLog[]>('/auditoria/', { params: filtros })
  return data
}

export async function fetchAuditPanel(params?: {
  fecha_desde?: string
  fecha_hasta?: string
}): Promise<MetricasAuditoria> {
  const { data } = await api.get<MetricasAuditoria>('/auditoria/metricas', { params })
  return data
}
