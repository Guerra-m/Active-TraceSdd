import { useQuery } from '@tanstack/react-query'
import { fetchMonitor } from '../services/academicoService'

export function useMonitor(comision_id: string) {
  return useQuery({
    queryKey: ['monitor', comision_id],
    queryFn: () => fetchMonitor(comision_id),
    enabled: !!comision_id,
  })
}
