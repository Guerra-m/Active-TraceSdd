import { api } from '@/shared/services/api'
import type { MonitorMetrics, MonitorFiltros } from '../types'

// Asignación seeded del admin (Programación I · Cohorte 2024-A) — fallback para COORDINADOR/ADMIN
const DEFAULT_ASIGNACION_ID = '8c17bf88-6eac-45c5-aff8-1bf59a17d9d0'
const DEFAULT_MATERIA_ID = 'e4ebc2e4-2c3d-408f-8994-f465bb8adc02'

export async function fetchMonitor(
  filtros?: MonitorFiltros,
  asignacionId?: string,
  materiaId?: string,
): Promise<MonitorMetrics> {
  const aid = asignacionId ?? DEFAULT_ASIGNACION_ID
  const mid = materiaId ?? DEFAULT_MATERIA_ID
  const { data } = await api.get<MonitorMetrics>(`/analisis/monitor/${aid}/${mid}`, { params: filtros })
  return data
}
