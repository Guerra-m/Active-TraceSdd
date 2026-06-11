import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useEncuentrosAdmin, useUpdateEncuentro } from './useEncuentrosAdmin'
import * as encuentrosService from '../services/encuentrosAdminService'
import type { EncuentroAdmin } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockEncuentro: EncuentroAdmin = {
  id: 'enc-1',
  tenant_id: 'tenant-1',
  slot_id: null,
  materia_id: 'mat-1',
  fecha: '2024-07-10',
  hora: '10:00',
  titulo: 'Encuentro semanal',
  estado: 'Programado',
  meet_url: null,
  video_url: null,
  comentario: null,
}

const mockList: EncuentroAdmin[] = [mockEncuentro]

describe('useEncuentrosAdmin', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna encuentros exitosamente', async () => {
    vi.spyOn(encuentrosService, 'fetchEncuentrosAdmin').mockResolvedValue(mockList)

    const { result } = renderHook(() => useEncuentrosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].titulo).toBe('Encuentro semanal')
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
    const updated = { ...mockEncuentro, estado: 'Realizado' as const }
    const spy = vi.spyOn(encuentrosService, 'updateEncuentro').mockResolvedValue(updated)

    const { result } = renderHook(() => useUpdateEncuentro(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'enc-1', payload: { estado: 'Realizado' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('enc-1', { estado: 'Realizado' })
  })
})
