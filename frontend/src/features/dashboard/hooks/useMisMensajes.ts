import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/services/api'

export interface MiMensaje {
  id: string
  asunto: string
  cuerpo: string
  estado: string
  materia_id: string | null
  enviado_at: string | null
  created_at: string
}

async function fetchMisMensajes(): Promise<MiMensaje[]> {
  const { data } = await api.get<MiMensaje[]>('/comunicaciones/mis-mensajes')
  return data
}

export function useMisMensajes() {
  return useQuery({
    queryKey: ['mis-mensajes'],
    queryFn: fetchMisMensajes,
    retry: false,
  })
}
