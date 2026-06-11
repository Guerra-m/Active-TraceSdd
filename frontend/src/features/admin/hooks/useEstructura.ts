import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchCarreras,
  createCarrera,
  updateCarrera,
  deleteCarrera,
  fetchCohortes,
  createCohorte,
  updateCohorte,
  deleteCohorte,
  fetchMaterias,
  createMateria,
  updateMateria,
  deleteMateria,
} from '../services/estructuraService'
import type {
  CreateCarreraPayload,
  UpdateCarreraPayload,
  CreateCohortePayload,
  UpdateCohortePayload,
  CreateMateriaPayload,
  UpdateMateriaPayload,
} from '../types'

export const CARRERAS_KEY = 'admin-carreras'
export const COHORTES_KEY = 'admin-cohortes'
export const MATERIAS_KEY = 'admin-materias'

// ─── Carreras ─────────────────────────────────────────────────────────────────

export function useCarreras() {
  return useQuery({ queryKey: [CARRERAS_KEY], queryFn: fetchCarreras })
}

export function useCreateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateCarreraPayload) => createCarrera(payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [CARRERAS_KEY] }),
  })
}

export function useUpdateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateCarreraPayload }) =>
      updateCarrera(id, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [CARRERAS_KEY] }),
  })
}

export function useDeleteCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteCarrera(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [CARRERAS_KEY] }),
  })
}

// ─── Cohortes ─────────────────────────────────────────────────────────────────

export function useCohortes() {
  return useQuery({ queryKey: [COHORTES_KEY], queryFn: fetchCohortes })
}

export function useCreateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateCohortePayload) => createCohorte(payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [COHORTES_KEY] }),
  })
}

export function useUpdateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateCohortePayload }) =>
      updateCohorte(id, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [COHORTES_KEY] }),
  })
}

export function useDeleteCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteCohorte(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [COHORTES_KEY] }),
  })
}

// ─── Materias ─────────────────────────────────────────────────────────────────

export function useMaterias() {
  return useQuery({ queryKey: [MATERIAS_KEY], queryFn: fetchMaterias })
}

export function useCreateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateMateriaPayload) => createMateria(payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [MATERIAS_KEY] }),
  })
}

export function useUpdateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateMateriaPayload }) =>
      updateMateria(id, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [MATERIAS_KEY] }),
  })
}

export function useDeleteMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteMateria(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: [MATERIAS_KEY] }),
  })
}
