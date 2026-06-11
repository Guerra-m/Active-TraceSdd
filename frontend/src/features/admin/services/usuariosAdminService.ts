import { api } from '@/shared/services/api'
import type { UsuarioAdmin, UpdateUsuarioAdminPayload } from '../types'

export async function fetchUsuariosAdmin(): Promise<UsuarioAdmin[]> {
  const { data } = await api.get<UsuarioAdmin[]>('/admin/usuarios')
  return data
}

export async function updateUsuarioAdmin(
  id: string,
  payload: UpdateUsuarioAdminPayload,
): Promise<UsuarioAdmin> {
  const { data } = await api.put<UsuarioAdmin>(`/admin/usuarios/${id}`, payload)
  return data
}
