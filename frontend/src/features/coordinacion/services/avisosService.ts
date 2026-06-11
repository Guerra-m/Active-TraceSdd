import { api } from '@/shared/services/api'
import type { Aviso, CreateAvisoPayload, UpdateAvisoPayload } from '../types'

export async function fetchAvisos(): Promise<Aviso[]> {
  const { data } = await api.get<Aviso[]>('/avisos')
  return data
}

export async function createAviso(payload: CreateAvisoPayload): Promise<Aviso> {
  const { data } = await api.post<Aviso>('/avisos', payload)
  return data
}

export async function updateAviso(id: string, payload: UpdateAvisoPayload): Promise<Aviso> {
  const { data } = await api.put<Aviso>(`/avisos/${id}`, payload)
  return data
}

export async function deleteAviso(id: string): Promise<void> {
  await api.delete(`/avisos/${id}`)
}

export async function ackAviso(id: string): Promise<void> {
  await api.post(`/avisos/${id}/ack`)
}
