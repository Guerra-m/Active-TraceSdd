import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useUsuariosAdmin, useUpdateUsuarioAdmin } from './useUsuariosAdmin'
import * as usuariosAdminService from '../services/usuariosAdminService'
import type { UsuarioAdmin } from '../types'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockUsuario: UsuarioAdmin = {
  id: 'usr-1',
  tenant_id: 'tenant-1',
  nombre: 'Juan',
  apellidos: 'Pérez',
  legajo: 'L001',
  estado: 'Activo',
  is_active: true,
  facturador: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockUsuarios: UsuarioAdmin[] = [mockUsuario]

describe('useUsuariosAdmin', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retorna la lista de usuarios exitosamente', async () => {
    vi.spyOn(usuariosAdminService, 'fetchUsuariosAdmin').mockResolvedValue(mockUsuarios)

    const { result } = renderHook(() => useUsuariosAdmin(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].nombre).toBe('Juan')
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

  it('llama a updateUsuarioAdmin con los parámetros correctos para desactivar', async () => {
    const usuarioInactivo: UsuarioAdmin = { ...mockUsuario, is_active: false, estado: 'Inactivo' }
    const spy = vi
      .spyOn(usuariosAdminService, 'updateUsuarioAdmin')
      .mockResolvedValue(usuarioInactivo)

    const { result } = renderHook(() => useUpdateUsuarioAdmin(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'usr-1', payload: { estado: 'Inactivo' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(spy).toHaveBeenCalledWith('usr-1', { estado: 'Inactivo' })
  })

  it('expone error si la actualización falla', async () => {
    vi.spyOn(usuariosAdminService, 'updateUsuarioAdmin').mockRejectedValue(
      new Error('Update error'),
    )

    const { result } = renderHook(() => useUpdateUsuarioAdmin(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'usr-1', payload: { estado: 'Inactivo' } })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
