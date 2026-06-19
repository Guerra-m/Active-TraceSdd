import { useQuery } from '@tanstack/react-query'
import { fetchMonitor } from '../services/monitorService'
import type { MonitorFiltros } from '../types'

export const MONITOR_KEY = 'coordinacion-monitor'

export function useMonitor(
  filtros?: MonitorFiltros,
  asignacionId?: string,
  materiaId?: string,
  enabled = true,
) {
  return useQuery({
    queryKey: [MONITOR_KEY, filtros, asignacionId, materiaId],
    queryFn: () => fetchMonitor(filtros, asignacionId, materiaId),
    enabled,
  })
}
