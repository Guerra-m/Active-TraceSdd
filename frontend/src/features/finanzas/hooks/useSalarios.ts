import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchSalariosBase,
  createSalarioBase,
  updateSalarioBase,
  fetchSalariosPlus,
  createSalarioPlus,
  updateSalarioPlus,
} from '../services/salariosService'
import type {
  CreateSalarioBasePayload,
  UpdateSalarioBasePayload,
  CreateSalarioPlusPayload,
  UpdateSalarioPlusPayload,
} from '../types'

export const SALARIOS_BASE_KEY = 'finanzas-salarios-base'
export const SALARIOS_PLUS_KEY = 'finanzas-salarios-plus'

// ─── Salario Base ─────────────────────────────────────────────────────────────

export function useSalariosBase() {
  return useQuery({
    queryKey: [SALARIOS_BASE_KEY],
    queryFn: fetchSalariosBase,
  })
}

export function useCreateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateSalarioBasePayload) => createSalarioBase(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SALARIOS_BASE_KEY] })
    },
  })
}

export function useUpdateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateSalarioBasePayload }) =>
      updateSalarioBase(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SALARIOS_BASE_KEY] })
    },
  })
}

// ─── Salario Plus ─────────────────────────────────────────────────────────────

export function useSalariosPlus() {
  return useQuery({
    queryKey: [SALARIOS_PLUS_KEY],
    queryFn: fetchSalariosPlus,
  })
}

export function useCreateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateSalarioPlusPayload) => createSalarioPlus(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SALARIOS_PLUS_KEY] })
    },
  })
}

export function useUpdateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateSalarioPlusPayload }) =>
      updateSalarioPlus(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SALARIOS_PLUS_KEY] })
    },
  })
}
