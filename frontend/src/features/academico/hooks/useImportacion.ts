import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchPreviewCalificaciones, postImportarCalificaciones } from '../services/academicoService'
import type { ImportacionPayload } from '../types'

export function usePreviewCalificaciones(comision_id: string) {
  return useQuery({
    queryKey: ['calificaciones-preview', comision_id],
    queryFn: () => fetchPreviewCalificaciones(comision_id),
    enabled: !!comision_id,
  })
}

export function useImportarCalificaciones() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ImportacionPayload) => postImportarCalificaciones(payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['atrasados', variables.comision_id] })
    },
  })
}
