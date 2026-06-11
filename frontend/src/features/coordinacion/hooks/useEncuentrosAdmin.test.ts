import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useEncuentrosAdmin, useUpdateEncuentro } from './useEncuentrosAdmin'
import * as encuentrosService from '../services/encuentrosAdminService'
import type { PagedResponse, EncuentroAdmin } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockEncuentro: EncuentroAdmin = {
  id: 'enc-1',
  alumno_id: 'al-1',
  alumno_nombre: 'Ana García',
  tutor_id: 'tut-1',
  tutor_nombre: 'Prof. López',
  fecha: '2024-07-10',
  hora: '10:00',
  tipo: 'individual',
  estado: 'programado',
  tenant_id: 'tenant-1',
}

const mockList: PagedResponse<EncuentroAdmin> = {
  items: [mockEncuentro],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useEncuentrosAdmin', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna encuentros exitosamente', async () => {
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    const { result } = renderHook(() => useEncuentrosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].alumno_nombre).toBe('Ana García')
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockRejectedValue(new Error('error'))

    const { result } = renderHook(() => useEncuentrosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useUpdateEncuentro', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('actualiza encuentro exitosamente', async () => {
    const updated = { ...mockEncuentro, estado: 'realizado' as const }
    const spy = vi.spyOn(encuentrosService, 'updateEncuentro').mockResolvedValue(updated)

    const { result } = renderHook(() => useUpdateEncuentro(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'enc-1', payload: { estado: 'realizado' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('enc-1', { estado: 'realizado' })
  })
})
