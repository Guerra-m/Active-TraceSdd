import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useTareas, useCreateTarea, useCambiarEstadoTarea } from './useTareas'
import * as tareasService from '../services/tareasService'
import type { Tarea } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockTarea: Tarea = {
  id: 'tar-1',
  tenant_id: 'tenant-1',
  materia_id: null,
  asignado_a: 'user-1',
  asignado_por: 'admin-1',
  estado: 'Pendiente',
  descripcion: 'Revisar planillas de notas',
  contexto_id: null,
  created_at: '2024-01-01T00:00:00Z',
}

const mockTareas: Tarea[] = [mockTarea]

describe('useTareas', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna tareas exitosamente', async () => {
    vi.spyOn(tareasService, 'fetchTareas').mockResolvedValue(mockTareas)

    const { result } = renderHook(() => useTareas(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].descripcion).toBe('Revisar planillas de notas')
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
    const updatedTarea = { ...mockTarea, estado: 'En progreso' as const }
    const spy = vi.spyOn(tareasService, 'cambiarEstadoTarea').mockResolvedValue(updatedTarea)

    const { result } = renderHook(() => useCambiarEstadoTarea(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'tar-1', payload: { estado: 'En progreso' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('tar-1', { estado: 'En progreso' })
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(tareasService, 'cambiarEstadoTarea').mockRejectedValue(new Error('bad transition'))

    const { result } = renderHook(() => useCambiarEstadoTarea(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'tar-1', payload: { estado: 'Cancelada' } })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
