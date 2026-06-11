import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchEncuentrosAdmin,
  crearSlot,
  updateEncuentro,
} from '../services/encuentrosAdminService'
import type { SlotEncuentroCreate, UpdateEncuentroPayload } from '../types'

export const ENCUENTROS_ADMIN_KEY = 'coordinacion-encuentros-admin'

export function useEncuentrosAdmin() {
  return useQuery({
    queryKey: [ENCUENTROS_ADMIN_KEY],
    queryFn: () => fetchEncuentrosAdmin(),
  })
}

export function useCrearSlot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SlotEncuentroCreate) => crearSlot(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ENCUENTROS_ADMIN_KEY] })
    },
  })
}

export function useUpdateEncuentro() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateEncuentroPayload }) =>
      updateEncuentro(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ENCUENTROS_ADMIN_KEY] })
    },
  })
}
