import { useQuery, useMutation } from '@tanstack/react-query'
import { postComunicacion, fetchEstadoComunicacion } from '../services/academicoService'
import type { ComunicacionPayload, EstadoComunicacion } from '../types'

const ESTADOS_FINALES: EstadoComunicacion[] = ['ENVIADO', 'FALLIDO', 'CANCELADO']

export function useEnviarComunicacion() {
  return useMutation({
    mutationFn: (payload: ComunicacionPayload) => postComunicacion(payload),
  })
}

export function useEstadoComunicacion(id: string | null) {
  return useQuery({
    queryKey: ['comunicacion-estado', id],
    queryFn: () => fetchEstadoComunicacion(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const estado = query.state.data?.estado
      if (!estado || ESTADOS_FINALES.includes(estado)) return false
      return 3000
    },
  })
}
