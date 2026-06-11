// ─── Equipos ──────────────────────────────────────────────────────────────────

export interface AsignacionItem {
  id: string
  tenant_id: string
  usuario_id: string
  rol: string
  materia_id: string | null
  carrera_id: string | null
  cohorte_id: string | null
  comisiones: string[]
  responsable_id: string | null
  desde: string
  hasta: string | null
  estado_vigencia: string
  created_at: string
  updated_at: string
}

export interface AsignacionMasivaPayload {
  usuario_ids: string[]
  rol: string
  materia_id?: string
  carrera_id?: string
  cohorte_id?: string
  comisiones?: string[]
  responsable_id?: string
  desde: string
  hasta?: string
}

export interface ClonarEquipoPayload {
  materia_id: string
  carrera_id: string
  cohorte_origen_id: string
  cohorte_destino_id: string
  desde: string
  hasta?: string
}

export interface VigenciaBulkPayload {
  materia_id: string
  carrera_id: string
  cohorte_id: string
  desde?: string
  hasta?: string
}

// ─── Avisos ───────────────────────────────────────────────────────────────────

export type AvisoAlcance = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol'
export type AvisoSeveridad = 'Info' | 'Advertencia' | 'Crítico'

export interface Aviso {
  id: string
  tenant_id: string
  alcance: AvisoAlcance
  materia_id: string | null
  cohorte_id: string | null
  rol_destino: string | null
  severidad: AvisoSeveridad
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en: string | null
  orden: number
  activo: boolean
  requiere_ack: boolean
}

export interface CreateAvisoPayload {
  alcance: AvisoAlcance
  materia_id?: string
  cohorte_id?: string
  rol_destino?: string
  severidad: AvisoSeveridad
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en?: string
  orden?: number
  activo?: boolean
  requiere_ack: boolean
}

export type UpdateAvisoPayload = Partial<CreateAvisoPayload>

// ─── Tareas ───────────────────────────────────────────────────────────────────

export type TareaEstado = 'Pendiente' | 'En progreso' | 'Resuelta' | 'Cancelada'

export interface Tarea {
  id: string
  tenant_id: string
  materia_id: string | null
  asignado_a: string
  asignado_por: string
  estado: TareaEstado
  descripcion: string
  contexto_id: string | null
  created_at: string
}

export interface Comentario {
  id: string
  tarea_id: string
  autor_id: string
  texto: string
  created_at: string
}

export interface CreateTareaPayload {
  asignado_a: string
  descripcion: string
  materia_id?: string
  contexto_id?: string
}

export interface CambiarEstadoPayload {
  estado: TareaEstado
}

export interface CreateComentarioPayload {
  texto: string
}

// ─── Monitor ──────────────────────────────────────────────────────────────────

export interface MonitorMetrics {
  total_alumnos: number
  atrasados: number
  al_dia: number
  promedio_general: number | null
  comunicaciones_enviadas: number
  comunicaciones_pendientes: number
}

export interface MonitorFiltros {
  desde?: string
  hasta?: string
}

// ─── Encuentros Admin ─────────────────────────────────────────────────────────

export type EncuentroEstado = 'Programado' | 'Realizado' | 'Cancelado'

export interface EncuentroAdmin {
  id: string
  tenant_id: string
  slot_id: string | null
  materia_id: string
  fecha: string
  hora: string
  titulo: string
  estado: EncuentroEstado
  meet_url: string | null
  video_url: string | null
  comentario: string | null
}

export interface SlotEncuentroCreate {
  materia_id: string
  titulo: string
  hora: string
  dia_semana?: string
  fecha_inicio?: string
  cant_semanas?: number
  fecha_unica?: string
  meet_url?: string
  vig_desde?: string
  vig_hasta?: string
}

export interface UpdateEncuentroPayload {
  estado?: EncuentroEstado
  meet_url?: string
  video_url?: string
  comentario?: string
}

// ─── Coloquios ────────────────────────────────────────────────────────────────

export interface EvaluacionItem {
  id: string
  tenant_id: string
  materia_id: string
  cohorte_id: string
  tipo: string
  instancia: string
  dias_disponibles: number
  cupos_por_dia: number
}

export interface MetricasColoquio {
  total_convocados: number
  instancias_activas: number
  reservas_activas: number
  notas_registradas: number
}

export interface CreateEvaluacionPayload {
  materia_id: string
  cohorte_id: string
  tipo: string
  instancia: string
  dias_disponibles: number
  cupos_por_dia: number
}

export interface ImportarAlumnosPayload {
  alumno_ids: string[]
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PageParams {
  page?: number
  page_size?: number
}

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
