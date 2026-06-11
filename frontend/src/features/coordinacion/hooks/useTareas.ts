import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchTareas,
  createTarea,
  cambiarEstadoTarea,
  fetchComentarios,
  createComentario,
} from '../services/tareasService'
import type { CreateTareaPayload, CambiarEstadoPayload, CreateComentarioPayload } from '../types'

export const TAREAS_KEY = 'coordinacion-tareas'
export const COMENTARIOS_KEY = 'coordinacion-comentarios'

export function useTareas() {
  return useQuery({
    queryKey: [TAREAS_KEY],
    queryFn: () => fetchTareas(),
  })
}

export function useCreateTarea() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTareaPayload) => createTarea(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TAREAS_KEY] })
    },
  })
}

export function useCambiarEstadoTarea() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CambiarEstadoPayload }) =>
      cambiarEstadoTarea(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TAREAS_KEY] })
    },
  })
}

export function useComentarios(tareaId: string) {
  return useQuery({
    queryKey: [COMENTARIOS_KEY, tareaId],
    queryFn: () => fetchComentarios(tareaId),
    enabled: !!tareaId,
  })
}

export function useCreateComentario(tareaId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateComentarioPayload) => createComentario(tareaId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [COMENTARIOS_KEY, tareaId] })
    },
  })
}
