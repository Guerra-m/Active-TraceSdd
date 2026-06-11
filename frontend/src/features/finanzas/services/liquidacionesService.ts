import { api } from '@/shared/services/api'
import type {
  Liquidacion,
  LiquidacionKPIs,
  LiquidacionPreview,
  CalcularLiquidacionPayload,
  LiquidacionFiltros,
  PagedResponse,
} from '../types'

export async function fetchLiquidaciones(
  filtros?: LiquidacionFiltros,
): Promise<PagedResponse<Liquidacion>> {
  const { data } = await api.get<PagedResponse<Liquidacion>>('/v1/liquidaciones/', {
    params: filtros,
  })
  return data
}

export async function fetchLiquidacionKPIs(filtros?: {
  cohorte_id?: string
  periodo?: string
}): Promise<LiquidacionKPIs> {
  const { data } = await api.get<LiquidacionKPIs>('/v1/liquidaciones/kpis', { params: filtros })
  return data
}

export async function calcularLiquidacion(
  payload: CalcularLiquidacionPayload,
): Promise<LiquidacionPreview> {
  const { data } = await api.post<LiquidacionPreview>('/v1/liquidaciones/calcular', payload)
  return data
}

export async function cerrarLiquidacion(id: string): Promise<Liquidacion> {
  const { data } = await api.post<Liquidacion>(`/v1/liquidaciones/${id}/cerrar`)
  return data
}
