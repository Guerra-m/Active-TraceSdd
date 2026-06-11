import { api } from '@/shared/services/api'
import type {
  EncuentroAdmin,
  SlotRecurrente,
  UpdateEncuentroPayload,
  PageParams,
  PagedResponse,
} from '../types'

export async function fetchEncuentrosAdmin(
  params?: PageParams,
): Promise<PagedResponse<EncuentroAdmin>> {
  const { data } = await api.get<PagedResponse<EncuentroAdmin>>('/encuentros', { params })
  return data
}

export async function crearSlotsRecurrentes(payload: SlotRecurrente): Promise<void> {
  await api.post('/encuentros/slots-recurrentes', payload)
}

export async function updateEncuentro(
  id: string,
  payload: UpdateEncuentroPayload,
): Promise<EncuentroAdmin> {
  const { data } = await api.patch<EncuentroAdmin>(`/encuentros/${id}`, payload)
  return data
}
