import { api } from '@/shared/services/api'
import type { Factura, CreateFacturaPayload, FacturaFiltros } from '../types'

export async function fetchFacturas(filtros?: FacturaFiltros): Promise<Factura[]> {
  const { data } = await api.get<Factura[]>('/facturas/', { params: filtros })
  return data
}

export async function createFactura(payload: CreateFacturaPayload): Promise<Factura> {
  const { data } = await api.post<Factura>('/facturas/', payload)
  return data
}

export async function abonarFactura(id: string, fecha_pago: string): Promise<Factura> {
  const { data } = await api.put<Factura>(`/facturas/${id}/abonar`, { fecha_pago })
  return data
}
