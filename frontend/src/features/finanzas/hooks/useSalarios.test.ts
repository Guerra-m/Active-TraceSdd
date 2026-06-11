import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import {
  useSalariosBase,
  useCreateSalarioBase,
  useSalariosPlus,
  useCreateSalarioPlus,
} from './useSalarios'
import * as salariosService from '../services/salariosService'
import type { SalarioBase, SalarioPlus } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockSalarioBase: SalarioBase = {
  id: 'sb-1',
  rol: 'TUTOR',
  monto: 80000,
  desde: '2024-01-01',
  hasta: null,
  tenant_id: 'tenant-1',
}

const mockSalarioPlus: SalarioPlus = {
  id: 'sp-1',
  rol: 'NEXO',
  monto: 30000,
  desde: '2024-01-01',
  hasta: null,
  tenant_id: 'tenant-1',
}

describe('useSalariosBase', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de salarios base exitosamente', async () => {
    vi.spyOn(salariosService, 'fetchSalariosBase').mockResolvedValue([mockSalarioBase])

    const { result } = renderHook(() => useSalariosBase(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].rol).toBe('TUTOR')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(salariosService, 'fetchSalariosBase').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useSalariosBase(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateSalarioBase', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createSalarioBase con los datos correctos', async () => {
    const spy = vi.spyOn(salariosService, 'createSalarioBase').mockResolvedValue(mockSalarioBase)

    const { result } = renderHook(() => useCreateSalarioBase(), { wrapper: createWrapper() })

    result.current.mutate({ rol: 'TUTOR', monto: 80000, desde: '2024-01-01' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ rol: 'TUTOR', monto: 80000, desde: '2024-01-01' })
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(salariosService, 'createSalarioBase').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateSalarioBase(), { wrapper: createWrapper() })

    result.current.mutate({ rol: 'TUTOR', monto: 80000, desde: '2024-01-01' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useSalariosPlus', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de salarios plus exitosamente', async () => {
    vi.spyOn(salariosService, 'fetchSalariosPlus').mockResolvedValue([mockSalarioPlus])

    const { result } = renderHook(() => useSalariosPlus(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].rol).toBe('NEXO')
  })

  it('expone error cuando el servicio de plus falla', async () => {
    vi.spyOn(salariosService, 'fetchSalariosPlus').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useSalariosPlus(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateSalarioPlus', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createSalarioPlus con los datos correctos', async () => {
    const spy = vi.spyOn(salariosService, 'createSalarioPlus').mockResolvedValue(mockSalarioPlus)

    const { result } = renderHook(() => useCreateSalarioPlus(), { wrapper: createWrapper() })

    result.current.mutate({ rol: 'NEXO', monto: 30000, desde: '2024-01-01' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ rol: 'NEXO', monto: 30000, desde: '2024-01-01' })
  })

  it('expone error si la creación de plus falla', async () => {
    vi.spyOn(salariosService, 'createSalarioPlus').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateSalarioPlus(), { wrapper: createWrapper() })

    result.current.mutate({ rol: 'NEXO', monto: 30000, desde: '2024-01-01' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
