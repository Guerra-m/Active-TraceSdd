import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useFacturas, useCreateFactura, useAbonarFactura } from './useFacturas'
import * as facturasService from '../services/facturasService'
import type { Factura, PagedResponse } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockFactura: Factura = {
  id: 'fac-1',
  docente_id: 'doc-1',
  docente_nombre: 'María García',
  monto: 95000,
  periodo: '2024-03',
  numero_factura: 'A-00001',
  estado: 'pendiente',
  fecha_emision: '2024-03-31',
  fecha_pago: null,
  tenant_id: 'tenant-1',
}

const mockPagedFacturas: PagedResponse<Factura> = {
  items: [mockFactura],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useFacturas', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de facturas exitosamente', async () => {
    vi.spyOn(facturasService, 'fetchFacturas').mockResolvedValue(mockPagedFacturas)

    const { result } = renderHook(() => useFacturas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].numero_factura).toBe('A-00001')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(facturasService, 'fetchFacturas').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useFacturas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateFactura', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createFactura con los parámetros correctos', async () => {
    const spy = vi.spyOn(facturasService, 'createFactura').mockResolvedValue(mockFactura)

    const { result } = renderHook(() => useCreateFactura(), { wrapper: createWrapper() })

    result.current.mutate({
      docente_id: 'doc-1',
      monto: 95000,
      periodo: '2024-03',
      numero_factura: 'A-00001',
      fecha_emision: '2024-03-31',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({
      docente_id: 'doc-1',
      monto: 95000,
      periodo: '2024-03',
      numero_factura: 'A-00001',
      fecha_emision: '2024-03-31',
    })
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(facturasService, 'createFactura').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateFactura(), { wrapper: createWrapper() })

    result.current.mutate({
      docente_id: 'doc-1',
      monto: 95000,
      periodo: '2024-03',
      numero_factura: 'A-00001',
      fecha_emision: '2024-03-31',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useAbonarFactura', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a abonarFactura con el id correcto', async () => {
    const abonada: Factura = { ...mockFactura, estado: 'abonada', fecha_pago: '2024-04-05' }
    const spy = vi.spyOn(facturasService, 'abonarFactura').mockResolvedValue(abonada)

    const { result } = renderHook(() => useAbonarFactura(), { wrapper: createWrapper() })

    result.current.mutate('fac-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('fac-1')
  })

  it('expone error si abonar falla', async () => {
    vi.spyOn(facturasService, 'abonarFactura').mockRejectedValue(new Error('Abonar error'))

    const { result } = renderHook(() => useAbonarFactura(), { wrapper: createWrapper() })

    result.current.mutate('fac-1')

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
