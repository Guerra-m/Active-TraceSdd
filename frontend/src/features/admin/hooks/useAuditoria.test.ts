import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useAuditLogs, useAuditPanel } from './useAuditoria'
import * as auditoriaService from '../services/auditoriaService'
import type { AuditLog, AuditPanel, PagedResponse } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockLog: AuditLog = {
  id: 'log-1',
  usuario_id: 'usr-1',
  usuario_nombre: 'Admin User',
  accion: 'LOGIN',
  recurso: 'auth',
  recurso_id: null,
  detalle: {},
  ip: '127.0.0.1',
  creado_en: '2024-03-15T10:00:00Z',
  tenant_id: 'tenant-1',
}

const mockPagedLogs: PagedResponse<AuditLog> = {
  items: [mockLog],
  total: 1,
  page: 1,
  page_size: 20,
}

const mockPanel: AuditPanel = {
  acciones_por_dia: [{ fecha: '2024-03-15', count: 10 }],
  comunicaciones_por_docente: [
    { docente_nombre: 'Juan Pérez', enviadas: 5, fallidas: 1 },
  ],
}

describe('useAuditLogs', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de logs de auditoría exitosamente', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditLogs').mockResolvedValue(mockPagedLogs)

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].accion).toBe('LOGIN')
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
    expect(result.current.data?.comunicaciones_por_docente[0].docente_nombre).toBe('Juan Pérez')
  })

  it('expone error cuando el panel falla', async () => {
    vi.spyOn(auditoriaService, 'fetchAuditPanel').mockRejectedValue(new Error('Panel error'))

    const { result } = renderHook(() => useAuditPanel(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
