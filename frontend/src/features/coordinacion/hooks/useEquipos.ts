import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchEquipos,
  asignacionMasiva,
  clonarEquipo,
  modificarVigenciaBulk,
  exportarEquipos,
} from '../services/equiposService'
import type {
  AsignacionMasivaPayload,
  ClonarEquipoPayload,
  VigenciaBulkPayload,
} from '../types'

export const EQUIPOS_KEY = 'coordinacion-equipos'

export function useEquipos() {
  return useQuery({
    queryKey: [EQUIPOS_KEY],
    queryFn: () => fetchEquipos(),
  })
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AsignacionMasivaPayload) => asignacionMasiva(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EQUIPOS_KEY] })
    },
  })
}

export function useClonarEquipo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClonarEquipoPayload) => clonarEquipo(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EQUIPOS_KEY] })
    },
  })
}

export function useModificarVigenciaBulk() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: VigenciaBulkPayload) => modificarVigenciaBulk(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EQUIPOS_KEY] })
    },
  })
}

export function useExportarEquipos() {
  return useMutation({
    mutationFn: exportarEquipos,
  })
}
