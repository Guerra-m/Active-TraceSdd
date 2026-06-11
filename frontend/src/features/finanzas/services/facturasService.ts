import { api } from '@/shared/services/api'
import type { Factura, CreateFacturaPayload, FacturaFiltros, PagedResponse } from '../types'

export async function fetchFacturas(filtros?: FacturaFiltros): Promise<PagedResponse<Factura>> {
  const { data } = await api.get<PagedResponse<Factura>>('/v1/facturas/', { params: filtros })
  return data
}

export async function createFactura(payload: CreateFacturaPayload): Promise<Factura> {
  const { data } = await api.post<Factura>('/v1/facturas/', payload)
  return data
}

export async function abonarFactura(id: string): Promise<Factura> {
  const { data } = await api.put<Factura>(`/v1/facturas/${id}/abonar`)
  return data
}
