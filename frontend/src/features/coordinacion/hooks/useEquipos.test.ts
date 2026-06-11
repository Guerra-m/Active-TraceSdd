import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useEquipos, useClonarEquipo } from './useEquipos'
import * as equiposService from '../services/equiposService'
import type { AsignacionItem } from '../types'
import type { ClonarEquipoResponse } from '../services/equiposService'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockAsignacion: AsignacionItem = {
  id: 'asi-1',
  tenant_id: 'tenant-1',
  usuario_id: 'user-1',
  rol: 'PROFESOR',
  materia_id: 'mat-1',
  carrera_id: 'car-1',
  cohorte_id: 'coh-1',
  comisiones: ['A'],
  responsable_id: null,
  desde: '2024-03-01',
  hasta: null,
  estado_vigencia: 'vigente',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('useEquipos', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de asignaciones exitosamente', async () => {
    vi.spyOn(equiposService, 'fetchEquipos').mockResolvedValue([mockAsignacion])

    const { result } = renderHook(() => useEquipos(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].rol).toBe('PROFESOR')
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
    const clonarResp: ClonarEquipoResponse = {
      creadas: 1,
      conflictos: 0,
      asignaciones: [{ ...mockAsignacion, id: 'asi-2', cohorte_id: 'coh-2' }],
      omitidos: [],
    }
    const spy = vi.spyOn(equiposService, 'clonarEquipo').mockResolvedValue(clonarResp)

    const { result } = renderHook(() => useClonarEquipo(), { wrapper: createWrapper() })

    result.current.mutate({
      materia_id: 'mat-1',
      carrera_id: 'car-1',
      cohorte_origen_id: 'coh-1',
      cohorte_destino_id: 'coh-2',
      desde: '2024-08-01',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith({
      materia_id: 'mat-1',
      carrera_id: 'car-1',
      cohorte_origen_id: 'coh-1',
      cohorte_destino_id: 'coh-2',
      desde: '2024-08-01',
    })
  })

  it('expone error si la clonación falla', async () => {
    vi.spyOn(equiposService, 'clonarEquipo').mockRejectedValue(new Error('Clonar error'))

    const { result } = renderHook(() => useClonarEquipo(), { wrapper: createWrapper() })

    result.current.mutate({
      materia_id: 'mat-1',
      carrera_id: 'car-1',
      cohorte_origen_id: 'coh-1',
      cohorte_destino_id: 'coh-2',
      desde: '2024-08-01',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
