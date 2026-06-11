import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUsuariosAdmin, updateUsuarioAdmin } from '../services/usuariosAdminService'
import type { UpdateUsuarioAdminPayload } from '../types'

export const USUARIOS_ADMIN_KEY = 'admin-usuarios'

export function useUsuariosAdmin(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: [USUARIOS_ADMIN_KEY, params],
    queryFn: () => fetchUsuariosAdmin(params),
  })
}

export function useUpdateUsuarioAdmin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateUsuarioAdminPayload }) =>
      updateUsuarioAdmin(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USUARIOS_ADMIN_KEY] })
    },
  })
}
