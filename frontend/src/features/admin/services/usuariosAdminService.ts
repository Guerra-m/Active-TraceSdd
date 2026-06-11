import { api } from '@/shared/services/api'
import type { UsuarioAdmin, UpdateUsuarioAdminPayload, PagedResponse } from '../types'

export async function fetchUsuariosAdmin(params?: {
  page?: number
  page_size?: number
}): Promise<PagedResponse<UsuarioAdmin>> {
  const { data } = await api.get<PagedResponse<UsuarioAdmin>>('/v1/admin/usuarios', { params })
  return data
}

export async function updateUsuarioAdmin(
  id: string,
  payload: UpdateUsuarioAdminPayload,
): Promise<UsuarioAdmin> {
  const { data } = await api.patch<UsuarioAdmin>(`/v1/admin/usuarios/${id}`, payload)
  return data
}
