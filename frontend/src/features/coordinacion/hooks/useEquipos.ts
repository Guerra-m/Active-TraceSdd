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
  PageParams,
} from '../types'

export const EQUIPOS_KEY = 'coordinacion-equipos'

export function useEquipos(params?: PageParams) {
  return useQuery({
    queryKey: [EQUIPOS_KEY, params],
    queryFn: () => fetchEquipos(params),
  })
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ equipoId, payload }: { equipoId: string; payload: AsignacionMasivaPayload }) =>
      asignacionMasiva(equipoId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [EQUIPOS_KEY] })
    },
  })
}

export function useClonarEquipo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ equipoId, payload }: { equipoId: string; payload: ClonarEquipoPayload }) =>
      clonarEquipo(equipoId, payload),
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
