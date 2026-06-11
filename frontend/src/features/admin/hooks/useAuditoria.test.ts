import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useAuditLogs, useAuditPanel } from './useAuditoria'
import * as auditoriaService from '../services/auditoriaService'
import type { AuditLog, MetricasAuditoria } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockLog: AuditLog = {
  id: 'log-1',
  tenant_id: 'tenant-1',
  fecha_hora: '2024-03-15T10:00:00Z',
  actor_id: 'usr-1',
  impersonado_id: null,
  materia_id: null,
  accion: 'LOGIN',
  detalle: {},
  filas_afectadas: null,
  ip: '127.0.0.1',
  user_agent: null,
}

const mockLogs: AuditLog[] = [mockLog]

const mockPanel: MetricasAuditoria = {
  acciones_por_dia: [{ fecha: '2024-03-15', total: 10 }],
  por_actor: [{ actor_id: 'usr-1', materia_id: null, total: 5 }],
}

describe('useAuditLogs', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de logs de auditoría exitosamente', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditLogs').mockResolvedValue(mockLogs)

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].accion).toBe('LOGIN')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditLogs').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useAuditPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna los datos del panel de auditoría exitosamente', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditPanel').mockResolvedValue(mockPanel)

    const { result } = renderHook(() => useAuditPanel(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.acciones_por_dia).toHaveLength(1)
    expect(result.current.data?.por_actor[0].actor_id).toBe('usr-1')
  })

  it('expone error cuando el panel falla', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditPanel').mockRejectedValue(new Error('Panel error'))

    const { result } = renderHook(() => useAuditPanel(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
