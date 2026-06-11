import { useQuery, useMutation } from '@tanstack/react-query'
import { postComunicacionPorCriterio, fetchLotesComunicacion } from '../services/academicoService'
import type { ComunicacionPorCriterioPayload } from '../types'

export function useEnviarComunicacion() {
  return useMutation({
    mutationFn: (payload: ComunicacionPorCriterioPayload) =>
      postComunicacionPorCriterio(payload),
  })
}

export function useLotesComunicacion() {
  return useQuery({
    queryKey: ['comunicacion-lotes'],
    queryFn: fetchLotesComunicacion,
  })
}
