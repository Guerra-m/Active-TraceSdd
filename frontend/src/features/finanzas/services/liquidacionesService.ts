import { api } from '@/shared/services/api'
import type {
  Liquidacion,
  LiquidacionKPIs,
  CalcularLiquidacionPayload,
  LiquidacionFiltros,
} from '../types'

export async function fetchLiquidaciones(filtros?: LiquidacionFiltros): Promise<Liquidacion[]> {
  const { data } = await api.get<Liquidacion[]>('/liquidaciones/', { params: filtros })
  return data
}

export async function fetchLiquidacionKPIs(filtros?: {
  cohorte_id?: string
  periodo?: string
}): Promise<LiquidacionKPIs> {
  const { data } = await api.get<LiquidacionKPIs>('/liquidaciones/kpis', { params: filtros })
  return data
}

export async function calcularLiquidacion(
  payload: CalcularLiquidacionPayload,
): Promise<Liquidacion[]> {
  const { data } = await api.post<Liquidacion[]>('/liquidaciones/calcular', payload)
  return data
}

export async function cerrarLiquidacion(id: string): Promise<Liquidacion> {
  const { data } = await api.post<Liquidacion>(`/liquidaciones/${id}/cerrar`)
  return data
}
