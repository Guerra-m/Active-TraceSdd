import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useUsuariosAdmin, useUpdateUsuarioAdmin } from './useUsuariosAdmin'
import * as usuariosAdminService from '../services/usuariosAdminService'
import type { UsuarioAdmin, PagedResponse } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockUsuario: UsuarioAdmin = {
  id: 'usr-1',
  email: 'juan@example.com',
  nombre: 'Juan Pérez',
  rol: 'TUTOR',
  activo: true,
  tenant_id: 'tenant-1',
}

const mockPagedUsuarios: PagedResponse<UsuarioAdmin> = {
  items: [mockUsuario],
  total: 1,
  page: 1,
  page_size: 20,
}

describe('useUsuariosAdmin', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de usuarios exitosamente', async () => {
    vi.spyOn(usuariosAdminService, 'fetchUsuariosAdmin').mockResolvedValue(mockPagedUsuarios)

    const { result } = renderHook(() => useUsuariosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].nombre).toBe('Juan Pérez')
  })

  it('expone error cuando el servicio falla', async () => {
    vi.spyOn(usuariosAdminService, 'fetchUsuariosAdmin').mockRejectedValue(
      new Error('Network error'),
    )

    const { result } = renderHook(() => useUsuariosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useUpdateUsuarioAdmin', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('llama a updateUsuarioAdmin con los parámetros correctos para activar/desactivar', async () => {
    const usuarioInactivo: UsuarioAdmin = { ...mockUsuario, activo: false }
    const spy = vi
      .spyOn(usuariosAdminService, 'updateUsuarioAdmin')
      .mockResolvedValue(usuarioInactivo)

    const { result } = renderHook(() => useUpdateUsuarioAdmin(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'usr-1', payload: { activo: false } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('usr-1', { activo: false })
  })

  it('expone error si la actualización falla', async () => {
    vi.spyOn(usuariosAdminService, 'updateUsuarioAdmin').mockRejectedValue(
      new Error('Update error'),
    )

    const { result } = renderHook(() => useUpdateUsuarioAdmin(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'usr-1', payload: { activo: false } })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
