import { useQuery } from '@tanstack/react-query'
import { fetchAtrasados, fetchRanking, fetchNotasFinales } from '../services/academicoService'

export function useAtrasados(comision_id: string) {
  return useQuery({
    queryKey: ['atrasados', comision_id],
    queryFn: () => fetchAtrasados(comision_id),
    enabled: !!comision_id,
  })
}

export function useRanking(comision_id: string) {
  return useQuery({
    queryKey: ['ranking', comision_id],
    queryFn: () => fetchRanking(comision_id),
    enabled: !!comision_id,
  })
}

export function useNotasFinales(comision_id: string) {
  return useQuery({
    queryKey: ['notas-finales', comision_id],
    queryFn: () => fetchNotasFinales(comision_id),
    enabled: !!comision_id,
  })
}
