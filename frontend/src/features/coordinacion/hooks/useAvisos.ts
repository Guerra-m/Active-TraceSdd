import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchAvisos,
  createAviso,
  updateAviso,
  deleteAviso,
  publicarAviso,
  ackAviso,
} from '../services/avisosService'
import type { AvisoEstado, CreateAvisoPayload, UpdateAvisoPayload, PageParams } from '../types'

export const AVISOS_KEY = 'coordinacion-avisos'

export function useAvisos(params?: PageParams & { estado?: AvisoEstado }) {
  return useQuery({
    queryKey: [AVISOS_KEY, params],
    queryFn: () => fetchAvisos(params),
  })
}

export function useCreateAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateAvisoPayload) => createAviso(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AVISOS_KEY] })
    },
  })
}

export function useUpdateAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateAvisoPayload }) =>
      updateAviso(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AVISOS_KEY] })
    },
  })
}

export function useDeleteAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAviso(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AVISOS_KEY] })
    },
  })
}

export function usePublicarAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => publicarAviso(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AVISOS_KEY] })
    },
  })
}

export function useAckAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => ackAviso(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AVISOS_KEY] })
    },
  })
}
