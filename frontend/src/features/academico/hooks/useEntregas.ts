import { useQuery } from '@tanstack/react-query'
import { fetchEntregasSinCorregir } from '../services/academicoService'

export function useEntregasSinCorregir(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['entregas-sin-corregir', asignacionId, materiaId],
    queryFn: () => fetchEntregasSinCorregir(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}
