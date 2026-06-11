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
  alumnos_atrasados: 5,
  entregas_pendientes: 12,
  comunicaciones_enviadas: 30,
  tasa_contacto: 0.85,
  resumen_por_materia: [
    {
      materia_id: 'mat-1',
      materia_nombre: 'Matemática I',
      atrasados: 3,
      al_dia: 20,
    },
  ],
}

describe('useMonitor', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna métricas del monitor exitosamente', async () => {
    vi.spyOn(monitorService, 'fetchMonitor').mockResolvedValue(mockMetrics)

    const { result } = renderHook(() => useMonitor(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.alumnos_atrasados).toBe(5)
    expect(result.current.data?.tasa_contacto).toBe(0.85)
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
