import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchLiquidaciones,
  fetchLiquidacionKPIs,
  calcularLiquidacion,
  cerrarLiquidacion,
} from '../services/liquidacionesService'
import type { CalcularLiquidacionPayload, LiquidacionFiltros } from '../types'

export const LIQUIDACIONES_KEY = 'finanzas-liquidaciones'
export const LIQUIDACION_KPIS_KEY = 'finanzas-liquidaciones-kpis'

export function useLiquidaciones(filtros?: LiquidacionFiltros) {
  return useQuery({
    queryKey: [LIQUIDACIONES_KEY, filtros],
    queryFn: () => fetchLiquidaciones(filtros),
  })
}

export function useLiquidacionKPIs(filtros?: { cohorte_id?: string; periodo?: string }) {
  return useQuery({
    queryKey: [LIQUIDACION_KPIS_KEY, filtros],
    queryFn: () => fetchLiquidacionKPIs(filtros),
  })
}

export function useCalcularLiquidacion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CalcularLiquidacionPayload) => calcularLiquidacion(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [LIQUIDACIONES_KEY] })
      void queryClient.invalidateQueries({ queryKey: [LIQUIDACION_KPIS_KEY] })
    },
  })
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => cerrarLiquidacion(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [LIQUIDACIONES_KEY] })
      void queryClient.invalidateQueries({ queryKey: [LIQUIDACION_KPIS_KEY] })
    },
  })
}
