import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchConvocatorias,
  createConvocatoria,
  importarAlumnos,
  fetchMetricas,
} from '../services/coloquiosService'
import type { CreateConvocatoriaPayload, ImportarAlumnosPayload, PageParams } from '../types'

export const CONVOCATORIAS_KEY = 'coordinacion-convocatorias'
export const METRICAS_KEY = 'coordinacion-metricas'

export function useConvocatorias(params?: PageParams) {
  return useQuery({
    queryKey: [CONVOCATORIAS_KEY, params],
    queryFn: () => fetchConvocatorias(params),
  })
}

export function useCreateConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateConvocatoriaPayload) => createConvocatoria(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CONVOCATORIAS_KEY] })
    },
  })
}

export function useImportarAlumnos(convocatoriaId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ImportarAlumnosPayload) => importarAlumnos(convocatoriaId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CONVOCATORIAS_KEY] })
    },
  })
}

export function useMetricasColoquio(convocatoriaId: string) {
  return useQuery({
    queryKey: [METRICAS_KEY, convocatoriaId],
    queryFn: () => fetchMetricas(convocatoriaId),
    enabled: !!convocatoriaId,
  })
}
