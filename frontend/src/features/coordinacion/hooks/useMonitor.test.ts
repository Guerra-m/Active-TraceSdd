import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useMonitor } from './useMonitor'
import * as monitorService from '../services/monitorService'
import type { MonitorMetrics } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockMetrics: MonitorMetrics = {
  total_alumnos: 25,
  atrasados: 5,
  al_dia: 20,
  promedio_general: 8.5,
  comunicaciones_enviadas: 30,
  comunicaciones_pendientes: 12,
}

describe('useMonitor', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna métricas del monitor exitosamente', async () => {
    vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)

    const { result } = renderHook(() => useMonitor(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.atrasados).toBe(5)
    expect(result.current.data?.promedio_general).toBe(8.5)
  })

  it('pasa filtros de fechas al servicio', async () => {
    const spy = vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)
    const filtros = { desde: '2024-01-01', hasta: '2024-06-30' }

    const { result } = renderHook(() => useMonitor(filtros), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith(filtros)
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(monitorService, 'fetchMonitor').mockRejectedValue(new Error('error'))

    const { result } = renderHook(() => useMonitor(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
