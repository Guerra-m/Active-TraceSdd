import { api } from '@/shared/services/api'
import type {
  Aviso,
  AvisoEstado,
  CreateAvisoPayload,
  UpdateAvisoPayload,
  PageParams,
  PagedResponse,
} from '../types'

export async function fetchAvisos(
  params?: PageParams & { estado?: AvisoEstado },
): Promise<PagedResponse<Aviso>> {
  const { data } = await api.get<PagedResponse<Aviso>>('/avisos', { params })
  return data
}

export async function createAviso(payload: CreateAvisoPayload): Promise<Aviso> {
  const { data } = await api.post<Aviso>('/avisos', payload)
  return data
}

export async function updateAviso(id: string, payload: UpdateAvisoPayload): Promise<Aviso> {
  const { data } = await api.patch<Aviso>(`/avisos/${id}`, payload)
  return data
}

export async function deleteAviso(id: string): Promise<void> {
  await api.delete(`/avisos/${id}`)
}

export async function publicarAviso(id: string): Promise<Aviso> {
  const { data } = await api.post<Aviso>(`/avisos/${id}/publicar`)
  return data
}

export async function ackAviso(id: string): Promise<void> {
  await api.post(`/avisos/${id}/ack`)
}
