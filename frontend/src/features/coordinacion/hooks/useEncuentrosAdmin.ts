import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchEncuentrosAdmin,
  crearSlotsRecurrentes,
  updateEncuentro,
} from '../services/encuentrosAdminService'
import type { SlotRecurrente, UpdateEncuentroPayload, PageParams } from '../types'

export const ENCUENTROS_ADMIN_KEY = 'coordinacion-encuentros-admin'

export function useEncuentrosAdmin(params?: PageParams) {
  return useQuery({
    queryKey: [ENCUENTROS_ADMIN_KEY, params],
    queryFn: () => fetchEncuentrosAdmin(params),
  })
}

export function useCrearSlotsRecurrentes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SlotRecurrente) => crearSlotsRecurrentes(payload),
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
