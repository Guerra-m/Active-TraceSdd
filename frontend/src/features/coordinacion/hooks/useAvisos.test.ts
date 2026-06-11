import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useAvisos, useCreateAviso, usePublicarAviso } from './useAvisos'
import * as avisosService from '../services/avisosService'
import type { PagedResponse, Aviso } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockAviso: Aviso = {
  id: 'av-1',
  titulo: 'Aviso importante',
  cuerpo: 'Contenido del aviso',
  scope: 'Global',
  estado: 'publicado',
  fecha_publicacion: '2024-06-01',
  fecha_expiracion: null,
  requiere_ack: false,
  leido_por_mi: false,
  tenant_id: 'tenant-1',
}

const mockAvisoList: PagedResponse<Aviso> = {
  items: [mockAviso],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useAvisos', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna lista de avisos exitosamente', async () => {
    vi.spyOn(avisosService, 'fetchAvisos').mockResolvedValue(mockAvisoList)

    const { result } = renderHook(() => useAvisos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].titulo).toBe('Aviso importante')
  })

  it('expone error si el servicio falla', async () => {
    vi.spyOn(avisosService, 'fetchAvisos').mockRejectedValue(new Error('fetch error'))

    const { result } = renderHook(() => useAvisos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateAviso', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('crea un aviso y retorna el objeto creado', async () => {
    const spy = vi.spyOn(avisosService, 'createAviso').mockResolvedValue(mockAviso)

    const { result } = renderHook(() => useCreateAviso(), { wrapper: createWrapper() })

    result.current.mutate({
      titulo: 'Aviso importante',
      cuerpo: 'Contenido',
      scope: 'Global',
      requiere_ack: false,
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledOnce()
    expect(result.current.data?.id).toBe('av-1')
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(avisosService, 'createAviso').mockRejectedValue(new Error('create error'))

    const { result } = renderHook(() => useCreateAviso(), { wrapper: createWrapper() })

    result.current.mutate({ titulo: '', cuerpo: '', scope: 'Global', requiere_ack: false })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('usePublicarAviso', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('publica un aviso exitosamente', async () => {
    const publicado = { ...mockAviso, estado: 'publicado' as const }
    const spy = vi.spyOn(avisosService, 'publicarAviso').mockResolvedValue(publicado)

    const { result } = renderHook(() => usePublicarAviso(), { wrapper: createWrapper() })

    result.current.mutate('av-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('av-1')
  })
})
