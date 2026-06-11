import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useEquipos, useClonarEquipo } from './useEquipos'
import * as equiposService from '../services/equiposService'
import type { PagedResponse, Equipo } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockEquipoList: PagedResponse<Equipo> = {
  items: [
    {
      id: 'eq-1',
      nombre: 'Equipo A',
      periodo: '2024-1',
      fecha_inicio: '2024-03-01',
      fecha_fin: '2024-07-31',
      tutores_count: 3,
      tenant_id: 'tenant-1',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useEquipos', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de equipos exitosamente', async () => {
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue(mockEquipoList)

    const { result } = renderHook(() => useEquipos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].nombre).toBe('Equipo A')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(equiposService, 'fetchEquipos').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useEquipos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useClonarEquipo', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a clonarEquipo con los parámetros correctos', async () => {
    const mockEquipo: Equipo = { ...mockEquipoList.items[0], id: 'eq-2', periodo: '2024-2' }
    const spy = vi.spyOn(equiposService, 'clonarEquipo').mockResolvedValue(mockEquipo)

    const { result } = renderHook(() => useClonarEquipo(), { wrapper: createWrapper() })

    result.current.mutate({ equipoId: 'eq-1', payload: { periodo_destino: '2024-2' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('eq-1', { periodo_destino: '2024-2' })
  })

  it('expone error si la clonación falla', async () => {
    vi.spyOn(equiposService, 'clonarEquipo').mockRejectedValue(new Error('Clonar error'))

    const { result } = renderHook(() => useClonarEquipo(), { wrapper: createWrapper() })

    result.current.mutate({ equipoId: 'eq-1', payload: { periodo_destino: '2024-2' } })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
