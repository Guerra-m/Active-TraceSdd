import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchFacturas, createFactura, abonarFactura } from '../services/facturasService'
import type { CreateFacturaPayload, FacturaFiltros } from '../types'

export const FACTURAS_KEY = 'finanzas-facturas'

export function useFacturas(filtros?: FacturaFiltros) {
  return useQuery({
    queryKey: [FACTURAS_KEY, filtros],
    queryFn: () => fetchFacturas(filtros),
  })
}

export function useCreateFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateFacturaPayload) => createFactura(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FACTURAS_KEY] })
    },
  })
}

export function useAbonarFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => abonarFactura(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [FACTURAS_KEY] })
    },
  })
}
