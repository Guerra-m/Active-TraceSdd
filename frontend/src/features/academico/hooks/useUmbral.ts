import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUmbral, putUmbral } from '../services/academicoService'
import type { UmbralPayload } from '../types'

export function useUmbral(asignacionId: string, materiaId: string) {
  return useQuery({
    queryKey: ['umbral', asignacionId, materiaId],
    queryFn: () => fetchUmbral(asignacionId, materiaId),
    enabled: !!asignacionId && !!materiaId,
  })
}

export function useActualizarUmbral(asignacionId: string, materiaId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UmbralPayload) => putUmbral(asignacionId, materiaId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['umbral', asignacionId, materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['mis-calificaciones'] })
    },
  })
}
