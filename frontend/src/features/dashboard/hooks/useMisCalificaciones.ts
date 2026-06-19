import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/services/api'

export interface MiCalificacion {
  actividad: string
  nota_numerica: number | null
  nota_textual: string | null
  aprobado: boolean
  materia_nombre: string | null
}

async function fetchMisCalificaciones(): Promise<MiCalificacion[]> {
  const { data } = await api.get<MiCalificacion[]>('/calificaciones/mis-calificaciones')
  return data
}

export function useMisCalificaciones() {
  return useQuery({
    queryKey: ['mis-calificaciones'],
    queryFn: fetchMisCalificaciones,
    retry: false,
  })
}
