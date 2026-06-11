import { api } from '@/shared/services/api'
import type {
  Equipo,
  AsignacionMasivaPayload,
  ClonarEquipoPayload,
  VigenciaBulkPayload,
  PageParams,
  PagedResponse,
} from '../types'

export async function fetchEquipos(params?: PageParams): Promise<PagedResponse<Equipo>> {
  const { data } = await api.get<PagedResponse<Equipo>>('/equipos', { params })
  return data
}

export async function asignacionMasiva(
  equipoId: string,
  payload: AsignacionMasivaPayload,
): Promise<void> {
  await api.post(`/equipos/${equipoId}/asignacion-masiva`, payload)
}

export async function clonarEquipo(
  equipoId: string,
  payload: ClonarEquipoPayload,
): Promise<Equipo> {
  const { data } = await api.post<Equipo>(`/equipos/${equipoId}/clonar`, payload)
  return data
}

export async function modificarVigenciaBulk(payload: VigenciaBulkPayload): Promise<void> {
  await api.patch('/equipos/vigencia-bulk', payload)
}

export async function exportarEquipos(): Promise<Blob> {
  const { data } = await api.get<Blob>('/equipos/exportar', {
    responseType: 'blob',
  })
  return data
}
