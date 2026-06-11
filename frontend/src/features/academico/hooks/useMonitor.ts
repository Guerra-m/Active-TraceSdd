import { useQuery } from '@tanstack/react-query'
import { fetchMonitor } from '../services/academicoService'

export function useMonitor(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['monitor', asignacionId, materiaId],
    queryFn: () => fetchMonitor(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}
