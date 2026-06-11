import { api } from '@/shared/services/api'
import type {
  Convocatoria,
  ConvocatoriaMetrics,
  CreateConvocatoriaPayload,
  ImportarAlumnosPayload,
  PageParams,
  PagedResponse,
} from '../types'

export async function fetchConvocatorias(
  params?: PageParams,
): Promise<PagedResponse<Convocatoria>> {
  const { data } = await api.get<PagedResponse<Convocatoria>>('/coloquios', { params })
  return data
}

export async function createConvocatoria(
  payload: CreateConvocatoriaPayload,
): Promise<Convocatoria> {
  const { data } = await api.post<Convocatoria>('/coloquios', payload)
  return data
}

export async function importarAlumnos(
  convocatoriaId: string,
  payload: ImportarAlumnosPayload,
): Promise<void> {
  await api.post(`/coloquios/${convocatoriaId}/alumnos`, payload)
}

export async function fetchMetricas(convocatoriaId: string): Promise<ConvocatoriaMetrics> {
  const { data } = await api.get<ConvocatoriaMetrics>(`/coloquios/${convocatoriaId}/metricas`)
  return data
}
