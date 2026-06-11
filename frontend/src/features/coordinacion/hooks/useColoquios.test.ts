import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useConvocatorias, useCreateConvocatoria, useMetricasColoquios } from './useColoquios'
import * as coloquiosService from '../services/coloquiosService'
import type { EvaluacionItem, MetricasColoquio } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockEvaluacion: EvaluacionItem = {
  id: 'ev-1',
  tenant_id: 'tenant-1',
  materia_id: 'mat-1',
  cohorte_id: 'coh-1',
  tipo: 'Coloquio',
  instancia: 'Coloquio 1er Cuatrimestre',
  dias_disponibles: 3,
  cupos_por_dia: 10,
}

const mockMetricas: MetricasColoquio = {
  total_convocados: 30,
  instancias_activas: 2,
  reservas_activas: 15,
  notas_registradas: 25,
}

describe('useConvocatorias', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna convocatorias exitosamente', async () => {
    vi.spyOn(coloquiosService, 'fetchConvocatorias').mockResolvedValue([mockEvaluacion])

    const { result } = renderHook(() => useConvocatorias(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].instancia).toBe('Coloquio 1er Cuatrimestre')
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
    const spy = vi.spyOn(coloquiosService, 'createConvocatoria').mockResolvedValue(mockEvaluacion)

    const { result } = renderHook(() => useCreateConvocatoria(), { wrapper: createWrapper() })

    result.current.mutate({
      materia_id: 'mat-1',
      cohorte_id: 'coh-1',
      tipo: 'Coloquio',
      instancia: 'Coloquio 1er Cuatrimestre',
      dias_disponibles: 3,
      cupos_por_dia: 10,
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledOnce()
  })
})

describe('useMetricasColoquios', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna métricas globales exitosamente', async () => {
    vi.spyOn(coloquiosService, 'fetchMetricas').mockResolvedValue(mockMetricas)

    const { result } = renderHook(() => useMetricasColoquios(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.instancias_activas).toBe(2)
    expect(result.current.data?.total_convocados).toBe(30)
  })
})
