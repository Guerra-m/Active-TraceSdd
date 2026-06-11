import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useTareas, useCreateTarea, useCambiarEstadoTarea } from './useTareas'
import * as tareasService from '../services/tareasService'
import type { PagedResponse, Tarea } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockTarea: Tarea = {
  id: 'tar-1',
  titulo: 'Revisar planillas',
  descripcion: 'Revisar planillas de notas',
  estado: 'pendiente',
  asignado_a: 'user-1',
  asignado_a_nombre: 'Juan Pérez',
  creado_por: 'admin-1',
  fecha_limite: '2024-07-01',
  tenant_id: 'tenant-1',
}

const mockTareaList: PagedResponse<Tarea> = {
  items: [mockTarea],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useTareas', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna tareas exitosamente', async () => {
    vi.spyOn(tareasService, 'fetchTareas').mockResolvedValue(mockTareaList)

    const { result } = renderHook(() => useTareas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].titulo).toBe('Revisar planillas')
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(tareasService, 'fetchTareas').mockRejectedValue(new Error('error'))

    const { result } = renderHook(() => useTareas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateTarea', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('crea tarea y retorna objeto creado', async () => {
    const spy = vi.spyOn(tareasService, 'createTarea').mockResolvedValue(mockTarea)

    const { result } = renderHook(() => useCreateTarea(), { wrapper: createWrapper() })

    result.current.mutate({
      titulo: 'Revisar planillas',
      descripcion: 'Revisar planillas de notas',
      asignado_a: 'user-1',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledOnce()
  })
})

describe('useCambiarEstadoTarea', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('cambia estado exitosamente', async () => {
    const updatedTarea = { ...mockTarea, estado: 'en_progreso' as const }
    const spy = vi.spyOn(tareasService, 'cambiarEstadoTarea').mockResolvedValue(updatedTarea)

    const { result } = renderHook(() => useCambiarEstadoTarea(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'tar-1', payload: { estado: 'en_progreso' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('tar-1', { estado: 'en_progreso' })
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(tareasService, 'cambiarEstadoTarea').mockRejectedValue(new Error('bad transition'))

    const { result } = renderHook(() => useCambiarEstadoTarea(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'tar-1', payload: { estado: 'cancelada' } })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
