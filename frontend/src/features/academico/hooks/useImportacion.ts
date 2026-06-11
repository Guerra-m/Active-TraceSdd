import { useMutation, useQueryClient } from '@tanstack/react-query'
import { postImportarCalificaciones } from '../services/academicoService'

interface ImportarPayload {
  asignacionId: string
  materiaId: string
  archivo: File
}

export function useImportarCalificaciones() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ asignacionId, materiaId, archivo }: ImportarPayload) =>
      postImportarCalificaciones(asignacionId, materiaId, archivo),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ['atrasados', variables.asignacionId, variables.materiaId],
      })
    },
  })
}
