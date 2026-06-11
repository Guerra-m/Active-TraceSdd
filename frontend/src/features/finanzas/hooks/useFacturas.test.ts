import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useFacturas, useCreateFactura, useAbonarFactura } from './useFacturas'
import * as facturasService from '../services/facturasService'
import type { Factura } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockFactura: Factura = {
  id: 'fac-1',
  tenant_id: 'tenant-1',
  usuario_id: 'usr-1',
  periodo: '2024-03',
  monto: 95000,
  detalle: 'Honorarios marzo',
  archivo_ref: null,
  estado: 'Pendiente',
  fecha_carga: '2024-03-31T00:00:00Z',
  fecha_pago: null,
  created_at: '2024-03-31T00:00:00Z',
  updated_at: '2024-03-31T00:00:00Z',
}

const mockFacturas: Factura[] = [mockFactura]

describe('useFacturas', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de facturas exitosamente', async () => {
    vi.spyOn(facturasService, 'fetchFacturas').mockResolvedValue(mockFacturas)

    const { result } = renderHook(() => useFacturas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].periodo).toBe('2024-03')
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
      usuario_id: 'usr-1',
      monto: 95000,
      periodo: '2024-03',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({
      usuario_id: 'usr-1',
      monto: 95000,
      periodo: '2024-03',
    })
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(facturasService, 'createFactura').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateFactura(), { wrapper: createWrapper() })

    result.current.mutate({
      usuario_id: 'usr-1',
      monto: 95000,
      periodo: '2024-03',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useAbonarFactura', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a abonarFactura con id y fecha_pago', async () => {
    const abonada: Factura = { ...mockFactura, estado: 'Abonada', fecha_pago: '2024-04-05' }
    const spy = vi.spyOn(facturasService, 'abonarFactura').mockResolvedValue(abonada)

    const { result } = renderHook(() => useAbonarFactura(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'fac-1', fecha_pago: '2024-04-05' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('fac-1', '2024-04-05')
  })

  it('expone error si abonar falla', async () => {
    vi.spyOn(facturasService, 'abonarFactura').mockRejectedValue(new Error('Abonar error'))

    const { result } = renderHook(() => useAbonarFactura(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'fac-1', fecha_pago: '2024-04-05' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
