import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUmbral, putUmbral } from '../services/academicoService'
import type { UmbralPayload } from '../types'

export function useUmbral(comision_id: string) {
  return useQuery({
    queryKey: ['umbral', comision_id],
    queryFn: () => fetchUmbral(comision_id),
    enabled: !!comision_id,
  })
}

export function useActualizarUmbral(umbral_id: string, comision_id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UmbralPayload) => putUmbral(umbral_id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['umbral', comision_id] })
    },
  })
}
