import { api } from '@/shared/services/api'
import type {
  EvaluacionItem,
  MetricasColoquio,
  CreateEvaluacionPayload,
  ImportarAlumnosPayload,
} from '../types'

export async function fetchConvocatorias(): Promise<EvaluacionItem[]> {
  const { data } = await api.get<EvaluacionItem[]>('/coloquios')
  return data
}

export async function createConvocatoria(payload: CreateEvaluacionPayload): Promise<EvaluacionItem> {
  const { data } = await api.post<EvaluacionItem>('/coloquios', payload)
  return data
}

export async function importarAlumnos(
  evaluacionId: string,
  payload: ImportarAlumnosPayload,
): Promise<{ importados: number; total_enviados: number }> {
  const { data } = await api.post<{ importados: number; total_enviados: number }>(
    `/coloquios/${evaluacionId}/alumnos`,
    payload,
  )
  return data
}

export async function fetchMetricas(): Promise<MetricasColoquio> {
  const { data } = await api.get<MetricasColoquio>('/coloquios/metricas')
  return data
}
