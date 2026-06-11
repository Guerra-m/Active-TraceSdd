import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchConvocatorias,
  createConvocatoria,
  importarAlumnos,
  fetchMetricas,
} from '../services/coloquiosService'
import type { CreateEvaluacionPayload, ImportarAlumnosPayload } from '../types'

export const CONVOCATORIAS_KEY = 'coordinacion-convocatorias'
export const METRICAS_KEY = 'coordinacion-coloquios-metricas'

export function useConvocatorias() {
  return useQuery({
    queryKey: [CONVOCATORIAS_KEY],
    queryFn: () => fetchConvocatorias(),
  })
}

export function useCreateConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateEvaluacionPayload) => createConvocatoria(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CONVOCATORIAS_KEY] })
    },
  })
}

export function useImportarAlumnos(evaluacionId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ImportarAlumnosPayload) => importarAlumnos(evaluacionId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CONVOCATORIAS_KEY] })
    },
  })
}

export function useMetricasColoquios() {
  return useQuery({
    queryKey: [METRICAS_KEY],
    queryFn: () => fetchMetricas(),
  })
}
