import { useQuery } from '@tanstack/react-query'
import { fetchEntregasSinCorregir } from '../services/academicoService'

export function useEntregasSinCorregir(comision_id: string) {
  return useQuery({
    queryKey: ['entregas-sin-corregir', comision_id],
    queryFn: () => fetchEntregasSinCorregir(comision_id),
    enabled: !!comision_id,
  })
}
