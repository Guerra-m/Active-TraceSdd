import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  postComunicacionPorCriterio,
  fetchLotesComunicacion,
  aprobarLote,
} from '../services/academicoService'
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

export function useAprobarLote() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (loteId: string) => aprobarLote(loteId),
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ['comunicacion-lotes'] }) },
  })
}
