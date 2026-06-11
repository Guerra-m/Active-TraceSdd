import { api } from '@/shared/services/api'
import type { MonitorMetrics, MonitorFiltros } from '../types'

export async function fetchMonitor(filtros?: MonitorFiltros): Promise<MonitorMetrics> {
  const { data } = await api.get<MonitorMetrics>('/analisis/monitor', { params: filtros })
  return data
}
