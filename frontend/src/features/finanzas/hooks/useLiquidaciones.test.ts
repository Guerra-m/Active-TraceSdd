import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import {
  useLiquidaciones,
  useLiquidacionKPIs,
  useCalcularLiquidacion,
  useCerrarLiquidacion,
} from './useLiquidaciones'
import * as liquidacionesService from '../services/liquidacionesService'
import type { PagedResponse, Liquidacion, LiquidacionKPIs, LiquidacionPreview } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockLiquidacion: Liquidacion = {
  id: 'liq-1',
  docente_id: 'doc-1',
  docente_nombre: 'Juan Pérez',
  tipo: 'general',
  cohorte_id: 'coh-1',
  periodo: '2024-03',
  monto_base: 100000,
  monto_plus: 20000,
  monto_total: 120000,
  estado: 'borrador',
  tenant_id: 'tenant-1',
}

const mockPagedLiquidaciones: PagedResponse<Liquidacion> = {
  items: [mockLiquidacion],
  total: 1,
  page: 1,
  page_size: 20,
}

const mockKPIs: LiquidacionKPIs = {
  total_general: 500000,
  total_nexo: 200000,
  total_facturantes: 150000,
  count_general: 5,
  count_nexo: 2,
  count_facturantes: 3,
}

describe('useLiquidaciones', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de liquidaciones exitosamente', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockResolvedValue(mockPagedLiquidaciones)

    const { result } = renderHook(() => useLiquidaciones(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].docente_nombre).toBe('Juan Pérez')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockRejectedValue(
      new Error('Network error'),
    )

    const { result } = renderHook(() => useLiquidaciones(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useLiquidacionKPIs', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna los KPIs exitosamente', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    const { result } = renderHook(() => useLiquidacionKPIs(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.total_general).toBe(500000)
    expect(result.current.data?.count_nexo).toBe(2)
  })

  it('expone error si falla la carga de KPIs', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockRejectedValue(
      new Error('KPI error'),
    )

    const { result } = renderHook(() => useLiquidacionKPIs(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCalcularLiquidacion', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a calcularLiquidacion con los parámetros correctos', async () => {
    const preview: LiquidacionPreview = { items: [mockLiquidacion], kpis: mockKPIs }
    const spy = vi
      .spyOn(liquidacionesService, 'calcularLiquidacion')
      .mockResolvedValue(preview)

    const { result } = renderHook(() => useCalcularLiquidacion(), { wrapper: createWrapper() })

    result.current.mutate({ cohorte_id: 'coh-1', periodo: '2024-03' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ cohorte_id: 'coh-1', periodo: '2024-03' })
  })

  it('expone error si el cálculo falla', async () => {
    vi.spyOn(liquidacionesService, 'calcularLiquidacion').mockRejectedValue(
      new Error('Calcular error'),
    )

    const { result } = renderHook(() => useCalcularLiquidacion(), { wrapper: createWrapper() })

    result.current.mutate({ cohorte_id: 'coh-1', periodo: '2024-03' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCerrarLiquidacion', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a cerrarLiquidacion con el id correcto', async () => {
    const cerrada: Liquidacion = { ...mockLiquidacion, estado: 'cerrada' }
    const spy = vi
      .spyOn(liquidacionesService, 'cerrarLiquidacion')
      .mockResolvedValue(cerrada)

    const { result } = renderHook(() => useCerrarLiquidacion(), { wrapper: createWrapper() })

    result.current.mutate('liq-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('liq-1')
  })

  it('expone error si el cierre falla', async () => {
    vi.spyOn(liquidacionesService, 'cerrarLiquidacion').mockRejectedValue(
      new Error('Cerrar error'),
    )

    const { result } = renderHook(() => useCerrarLiquidacion(), { wrapper: createWrapper() })

    result.current.mutate('liq-1')

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
