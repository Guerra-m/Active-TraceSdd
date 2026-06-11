import { useQuery } from '@tanstack/react-query'
import { fetchAtrasados, fetchRanking, fetchNotasFinales } from '../services/academicoService'

export function useAtrasados(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['atrasados', asignacionId, materiaId],
    queryFn: () => fetchAtrasados(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}

export function useRanking(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['ranking', asignacionId, materiaId],
    queryFn: () => fetchRanking(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}

export function useNotasFinales(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['notas-finales', asignacionId, materiaId],
    queryFn: () => fetchNotasFinales(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}
