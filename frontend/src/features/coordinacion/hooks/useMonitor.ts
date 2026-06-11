import { useQuery } from '@tanstack/react-query'
import { fetchMonitor } from '../services/monitorService'
import type { MonitorFiltros } from '../types'

export const MONITOR_KEY = 'coordinacion-monitor'

export function useMonitor(filtros?: MonitorFiltros) {
  return useQuery({
    queryKey: [MONITOR_KEY, filtros],
    queryFn: () => fetchMonitor(filtros),
  })
}
