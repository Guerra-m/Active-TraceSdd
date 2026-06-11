import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useConvocatorias, useCreateConvocatoria, useMetricasColoquio } from './useColoquios'
import * as coloquiosService from '../services/coloquiosService'
import type { PagedResponse, Convocatoria, ConvocatoriaMetrics } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockConvocatoria: Convocatoria = {
  id: 'conv-1',
  materia_id: 'mat-1',
  materia_nombre: 'Matemática I',
  fecha: '2024-07-20',
  cupo: 30,
  inscriptos: 15,
  descripcion: 'Coloquio primer cuatrimestre',
  estado: 'abierta',
  tenant_id: 'tenant-1',
}

const mockConvList: PagedResponse<Convocatoria> = {
  items: [mockConvocatoria],
  total: 1,
  page: 1,
  page_size: 20,
}

const mockMetricas: ConvocatoriaMetrics = {
  convocatoria_id: 'conv-1',
  aprobados: 10,
  desaprobados: 3,
  ausentes: 2,
  nota_promedio: 7.5,
}

describe('useConvocatorias', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna convocatorias exitosamente', async () => {
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue(mockConvList)

    const { result } = renderHook(() => useConvocatorias(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].materia_nombre).toBe('Matemática I')
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockRejectedValue(new Error('error'))

    const { result } = renderHook(() => useConvocatorias(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateConvocatoria', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('crea convocatoria exitosamente', async () => {
    const spy = vi.spyOn(coloquiosService, 'createConvocatoria').mockResolvedValue(mockConvocatoria)

    const { result } = renderHook(() => useCreateConvocatoria(), { wrapper: createWrapper() })

    result.current.mutate({
      materia_id: 'mat-1',
      fecha: '2024-07-20',
      cupo: 30,
      descripcion: 'Coloquio primer cuatrimestre',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledOnce()
  })
})

describe('useMetricasColoquio', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna métricas cuando convocatoriaId es válido', async () => {
    vi.spyOn(coloquiosService, 'fetchMetricas').mockResolvedValue(mockMetricas)

    const { result } = renderHook(() => useMetricasColoquio('conv-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.aprobados).toBe(10)
    expect(result.current.data?.nota_promedio).toBe(7.5)
  })
})
