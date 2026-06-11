import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import {
  useCarreras,
  useCreateCarrera,
  useCohortes,
  useCreateCohorte,
  useMaterias,
  useCreateMateria,
} from './useEstructura'
import * as estructuraService from '../services/estructuraService'
import type { Carrera, Cohorte, Materia } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockCarrera: Carrera = {
  id: 'car-1',
  nombre: 'Ingeniería en Sistemas',
  codigo: 'ISI',
  activa: true,
  tenant_id: 'tenant-1',
}

const mockCohorte: Cohorte = {
  id: 'coh-1',
  carrera_id: 'car-1',
  carrera_nombre: 'Ingeniería en Sistemas',
  anio: 2024,
  periodo: '2024-1',
  activa: true,
  tenant_id: 'tenant-1',
}

const mockMateria: Materia = {
  id: 'mat-1',
  nombre: 'Algoritmos',
  codigo: 'ALG',
  carrera_id: 'car-1',
  carrera_nombre: 'Ingeniería en Sistemas',
  grupo_plus: null,
  activa: true,
  tenant_id: 'tenant-1',
}

describe('useCarreras', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de carreras exitosamente', async () => {
    vi.spyOn(estructuraService, 'fetchCarreras').mockResolvedValue([mockCarrera])

    const { result } = renderHook(() => useCarreras(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].nombre).toBe('Ingeniería en Sistemas')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(estructuraService, 'fetchCarreras').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useCarreras(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateCarrera', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createCarrera con los datos correctos', async () => {
    const spy = vi.spyOn(estructuraService, 'createCarrera').mockResolvedValue(mockCarrera)

    const { result } = renderHook(() => useCreateCarrera(), { wrapper: createWrapper() })

    result.current.mutate({ nombre: 'Ingeniería en Sistemas', codigo: 'ISI' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ nombre: 'Ingeniería en Sistemas', codigo: 'ISI' })
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(estructuraService, 'createCarrera').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateCarrera(), { wrapper: createWrapper() })

    result.current.mutate({ nombre: 'Test', codigo: 'TST' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCohortes', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de cohortes exitosamente', async () => {
    vi.spyOn(estructuraService, 'fetchCohortes').mockResolvedValue([mockCohorte])

    const { result } = renderHook(() => useCohortes(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].periodo).toBe('2024-1')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(estructuraService, 'fetchCohortes').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useCohortes(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateCohorte', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createCohorte con los datos correctos', async () => {
    const spy = vi.spyOn(estructuraService, 'createCohorte').mockResolvedValue(mockCohorte)

    const { result } = renderHook(() => useCreateCohorte(), { wrapper: createWrapper() })

    result.current.mutate({ carrera_id: 'car-1', anio: 2024, periodo: '2024-1' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ carrera_id: 'car-1', anio: 2024, periodo: '2024-1' })
  })

  it('expone error si la creación falla', async () => {
    vi.spyOn(estructuraService, 'createCohorte').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateCohorte(), { wrapper: createWrapper() })

    result.current.mutate({ carrera_id: 'car-1', anio: 2024, periodo: '2024-1' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useMaterias', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de materias exitosamente', async () => {
    vi.spyOn(estructuraService, 'fetchMaterias').mockResolvedValue([mockMateria])

    const { result } = renderHook(() => useMaterias(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].nombre).toBe('Algoritmos')
  })

  it('expone error cuando el servicio de materias falla', async () => {
    vi.spyOn(estructuraService, 'fetchMaterias').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useMaterias(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateMateria', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a createMateria con los datos correctos incluyendo grupo_plus', async () => {
    const materiaConPlus: Materia = { ...mockMateria, grupo_plus: 'G1' }
    const spy = vi.spyOn(estructuraService, 'createMateria').mockResolvedValue(materiaConPlus)

    const { result } = renderHook(() => useCreateMateria(), { wrapper: createWrapper() })

    result.current.mutate({ nombre: 'Algoritmos', codigo: 'ALG', carrera_id: 'car-1', grupo_plus: 'G1' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({ nombre: 'Algoritmos', codigo: 'ALG', carrera_id: 'car-1', grupo_plus: 'G1' })
  })

  it('expone error si la creación de materia falla', async () => {
    vi.spyOn(estructuraService, 'createMateria').mockRejectedValue(new Error('Create error'))

    const { result } = renderHook(() => useCreateMateria(), { wrapper: createWrapper() })

    result.current.mutate({ nombre: 'Test', codigo: 'TST', carrera_id: 'car-1' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
