import { api } from '@/shared/services/api'
import type {
  ActividadPreview,
  ImportacionPayload,
  ImportacionResult,
  Umbral,
  UmbralPayload,
  AlumnoAtrasado,
  AlumnoRanking,
  AlumnoNotaFinal,
  EntregaSinCorregir,
  ComunicacionPayload,
  ComunicacionResponse,
  ComunicacionEstado,
  MonitorData,
} from '../types'

// ─── Calificaciones ───────────────────────────────────────────────────────────

export async function fetchPreviewCalificaciones(comision_id: string): Promise<ActividadPreview[]> {
  const { data } = await api.get<ActividadPreview[]>('/calificaciones/preview', {
    params: { comision_id },
  })
  return data
}

export async function postImportarCalificaciones(payload: ImportacionPayload): Promise<ImportacionResult> {
  const { data } = await api.post<ImportacionResult>('/calificaciones/import', payload)
  return data
}

// ─── Umbral ───────────────────────────────────────────────────────────────────

export async function fetchUmbral(comision_id: string): Promise<Umbral> {
  const { data } = await api.get<Umbral>('/umbrales', { params: { comision_id } })
  return data
}

export async function putUmbral(id: string, payload: UmbralPayload): Promise<Umbral> {
  const { data } = await api.put<Umbral>(`/umbrales/${id}`, payload)
  return data
}

// ─── Atrasados ────────────────────────────────────────────────────────────────

export async function fetchAtrasados(comision_id: string): Promise<AlumnoAtrasado[]> {
  const { data } = await api.get<AlumnoAtrasado[]>('/analisis/atrasados', {
    params: { comision_id },
  })
  return data
}

export async function fetchRanking(comision_id: string): Promise<AlumnoRanking[]> {
  const { data } = await api.get<AlumnoRanking[]>('/analisis/ranking', {
    params: { comision_id },
  })
  return data
}

export async function fetchNotasFinales(comision_id: string): Promise<AlumnoNotaFinal[]> {
  const { data } = await api.get<AlumnoNotaFinal[]>('/analisis/notas-finales', {
    params: { comision_id },
  })
  return data
}

// ─── Entregas sin corregir ────────────────────────────────────────────────────

export async function fetchEntregasSinCorregir(comision_id: string): Promise<EntregaSinCorregir[]> {
  const { data } = await api.get<EntregaSinCorregir[]>('/analisis/entregas-sin-corregir', {
    params: { comision_id },
  })
  return data
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export async function postComunicacion(payload: ComunicacionPayload): Promise<ComunicacionResponse> {
  const { data } = await api.post<ComunicacionResponse>('/comunicaciones/', payload)
  return data
}

export async function fetchEstadoComunicacion(id: string): Promise<ComunicacionEstado> {
  const { data } = await api.get<ComunicacionEstado>(`/comunicaciones/${id}/estado`)
  return data
}

// ─── Monitor ─────────────────────────────────────────────────────────────────

export async function fetchMonitor(comision_id: string): Promise<MonitorData> {
  const { data } = await api.get<MonitorData>('/analisis/monitor', {
    params: { comision_id },
  })
  return data
}
