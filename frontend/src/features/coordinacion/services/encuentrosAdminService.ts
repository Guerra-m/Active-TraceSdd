import { api } from '@/shared/services/api'
import type { EncuentroAdmin, SlotEncuentroCreate, UpdateEncuentroPayload } from '../types'

export async function fetchEncuentrosAdmin(): Promise<EncuentroAdmin[]> {
  const { data } = await api.get<EncuentroAdmin[]>('/encuentros')
  return data
}

export async function crearSlot(payload: SlotEncuentroCreate): Promise<void> {
  await api.post('/encuentros/slots', payload)
}

export async function updateEncuentro(
  id: string,
  payload: UpdateEncuentroPayload,
): Promise<EncuentroAdmin> {
  const { data } = await api.patch<EncuentroAdmin>(`/encuentros/${id}`, payload)
  return data
}
