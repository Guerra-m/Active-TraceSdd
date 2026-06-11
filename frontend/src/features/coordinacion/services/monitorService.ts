import { api } from '@/shared/services/api'
import type { MonitorMetrics, MonitorFiltros } from '../types'

// Usa la asignación seeded del docente admin (Programacion I - Cohorte 2024-A)
const DEFAULT_ASIGNACION_ID = '094c9029-321d-41a4-8f00-9f99437c0581'
const DEFAULT_MATERIA_ID = '9a1ac748-7387-49dd-a1dd-4f06c2d2181b'

export async function fetchMonitor(filtros?: MonitorFiltros): Promise<MonitorMetrics> {
  const { data } = await api.get<MonitorMetrics>(
    `/analisis/monitor/${DEFAULT_ASIGNACION_ID}/${DEFAULT_MATERIA_ID}`,
    { params: filtros },
  )
  return data
}
