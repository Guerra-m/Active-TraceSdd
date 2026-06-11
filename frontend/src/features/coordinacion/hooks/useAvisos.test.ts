import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useAvisos, useCreateAviso } from './useAvisos'
import * as avisosService from '../services/avisosService'
import type { Aviso } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockAviso: Aviso = {
  id: 'av-1',
  tenant_id: 'tenant-1',
  alcance: 'Global',
  materia_id: null,
  cohorte_id: null,
  rol_destino: null,
  severidad: 'Info',
  titulo: 'Aviso importante',
  cuerpo: 'Contenido del aviso',
  inicio_en: '2024-06-01T00:00:00Z',
  fin_en: null,
  orden: 0,
  activo: true,
  requiere_ack: false,
}

const mockAvisos: Aviso[] = [mockAviso]

describe('useAvisos', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna lista de avisos exitosamente', async () => {
    vi.spyOn(avisosService, 'fetchAvisos').mockResolvedValue(mockAvisos)

    const { result } = renderHook(() => useAvisos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].titulo).toBe('Aviso importante')
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
      alcance: 'Global',
      severidad: 'Info',
      inicio_en: '2024-06-01T00:00:00Z',
      activo: true,
      requiere_ack: false,
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledOnce()
    expect(result.current.data?.id).toBe('av-1')
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(avisosService, 'createAviso').mockRejectedValue(new Error('create error'))

    const { result } = renderHook(() => useCreateAviso(), { wrapper: createWrapper() })

    result.current.mutate({
      titulo: '',
      cuerpo: '',
      alcance: 'Global',
      severidad: 'Info',
      inicio_en: '2024-06-01T00:00:00Z',
      activo: true,
      requiere_ack: false,
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
