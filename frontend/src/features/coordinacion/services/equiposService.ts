import { api } from '@/shared/services/api'
import type {
  AsignacionItem,
  AsignacionMasivaPayload,
  ClonarEquipoPayload,
  VigenciaBulkPayload,
} from '../types'

export interface ClonarEquipoResponse {
  creadas: number
  conflictos: number
  asignaciones: AsignacionItem[]
  omitidos: AsignacionItem[]
}

export async function fetchEquipos(): Promise<AsignacionItem[]> {
  const { data } = await api.get<AsignacionItem[]>('/equipos')
  return data
}

export async function asignacionMasiva(payload: AsignacionMasivaPayload): Promise<void> {
  await api.post('/equipos/masiva', payload)
}

export async function clonarEquipo(payload: ClonarEquipoPayload): Promise<ClonarEquipoResponse> {
  const { data } = await api.post<ClonarEquipoResponse>('/equipos/clonar', payload)
  return data
}

export async function modificarVigenciaBulk(payload: VigenciaBulkPayload): Promise<void> {
  await api.patch('/equipos/vigencia', payload)
}

export async function exportarEquipos(): Promise<Blob> {
  const { data } = await api.get<Blob>('/equipos/exportar', { responseType: 'blob' })
  return data
}
