import { api } from '@/shared/services/api'
import type {
  AtrasadosResponse,
  RankingResponse,
  NotasFinalesResponse,
  UmbralResponse,
  UmbralPayload,
  ImportarCalificacionesResponse,
  EntregasSinCorregirResponse,
  ComunicacionPorCriterioPayload,
  LoteComunicacionResponse,
  MonitorData,
} from '../types'

// ─── Analisis ─────────────────────────────────────────────────────────────────

export async function fetchAtrasados(
  asignacionId: string,
  materiaId: string,
): Promise<AtrasadosResponse> {
  const { data } = await api.get<AtrasadosResponse>(
    `/analisis/atrasados/${asignacionId}/${materiaId}`,
  )
  return data
}

export async function fetchRanking(
  asignacionId: string,
  materiaId: string,
): Promise<RankingResponse> {
  const { data } = await api.get<RankingResponse>(
    `/analisis/ranking/${asignacionId}/${materiaId}`,
  )
  return data
}

export async function fetchNotasFinales(
  asignacionId: string,
  materiaId: string,
): Promise<NotasFinalesResponse> {
  const { data } = await api.get<NotasFinalesResponse>(
    `/analisis/notas-finales/${asignacionId}/${materiaId}`,
  )
  return data
}

export async function fetchEntregasSinCorregir(
  asignacionId: string,
  materiaId: string,
): Promise<EntregasSinCorregirResponse> {
  const { data } = await api.get<EntregasSinCorregirResponse>(
    `/analisis/entregas-sin-corregir/${asignacionId}/${materiaId}`,
  )
  return data
}

export async function fetchMonitor(
  asignacionId: string,
  materiaId: string,
): Promise<MonitorData> {
  const { data } = await api.get<MonitorData>(
    `/analisis/monitor/${asignacionId}/${materiaId}`,
  )
  return data
}

// ─── Umbral ───────────────────────────────────────────────────────────────────

export async function fetchUmbral(
  asignacionId: string,
  materiaId: string,
): Promise<UmbralResponse> {
  const { data } = await api.get<UmbralResponse>(
    `/calificaciones/umbral/${asignacionId}/${materiaId}`,
  )
  return data
}

export async function putUmbral(
  asignacionId: string,
  materiaId: string,
  payload: UmbralPayload,
): Promise<UmbralResponse> {
  const { data } = await api.put<UmbralResponse>(
    `/calificaciones/umbral/${asignacionId}/${materiaId}`,
    payload,
  )
  return data
}

// ─── Importación ──────────────────────────────────────────────────────────────

export async function postImportarCalificaciones(
  asignacionId: string,
  materiaId: string,
  archivo: File,
): Promise<ImportarCalificacionesResponse> {
  const form = new FormData()
  form.append('archivo', archivo)
  form.append('asignacion_id', asignacionId)
  form.append('materia_id', materiaId)
  const { data } = await api.post<ImportarCalificacionesResponse>(
    '/calificaciones/importar',
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export async function postComunicacionPorCriterio(
  payload: ComunicacionPorCriterioPayload,
): Promise<LoteComunicacionResponse> {
  const { data } = await api.post<LoteComunicacionResponse>(
    '/comunicaciones/lotes/por-criterio',
    payload,
  )
  return data
}

export async function fetchLotesComunicacion(): Promise<LoteComunicacionResponse[]> {
  const { data } = await api.get<LoteComunicacionResponse[]>('/comunicaciones/lotes')
  return data
}
