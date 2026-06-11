// ─── Equipos ──────────────────────────────────────────────────────────────────

export interface Equipo {
  id: string
  nombre: string
  periodo: string
  fecha_inicio: string
  fecha_fin: string
  tutores_count: number
  tenant_id: string
}

export interface AsignacionMasivaPayload {
  tutor_id: string
  alumno_ids: string[]
}

export interface ClonarEquipoPayload {
  periodo_destino: string
}

export interface VigenciaBulkPayload {
  equipo_ids: string[]
  fecha_inicio: string
  fecha_fin: string
}

// ─── Avisos ───────────────────────────────────────────────────────────────────

export type AvisoScope = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol'
export type AvisoEstado = 'borrador' | 'publicado' | 'expirado'

export interface Aviso {
  id: string
  titulo: string
  cuerpo: string
  scope: AvisoScope
  estado: AvisoEstado
  fecha_publicacion: string | null
  fecha_expiracion: string | null
  requiere_ack: boolean
  leido_por_mi: boolean
  tenant_id: string
}

export interface CreateAvisoPayload {
  titulo: string
  cuerpo: string
  scope: AvisoScope
  fecha_expiracion?: string
  requiere_ack: boolean
}

export type UpdateAvisoPayload = Partial<CreateAvisoPayload>

// ─── Tareas ───────────────────────────────────────────────────────────────────

export type TareaEstado = 'pendiente' | 'en_progreso' | 'completada' | 'cancelada'

export interface Tarea {
  id: string
  titulo: string
  descripcion: string
  estado: TareaEstado
  asignado_a: string
  asignado_a_nombre: string
  creado_por: string
  fecha_limite: string | null
  tenant_id: string
}

export interface Comentario {
  id: string
  tarea_id: string
  autor_id: string
  autor_nombre: string
  contenido: string
  creado_en: string
}

export interface CreateTareaPayload {
  titulo: string
  descripcion: string
  asignado_a: string
  fecha_limite?: string
}

export interface DelegarTareaPayload {
  nuevo_asignado: string
}

export interface CambiarEstadoPayload {
  estado: TareaEstado
}

export interface CreateComentarioPayload {
  contenido: string
}

// ─── Monitor ──────────────────────────────────────────────────────────────────

export interface MonitorMetrics {
  alumnos_atrasados: number
  entregas_pendientes: number
  comunicaciones_enviadas: number
  tasa_contacto: number
  resumen_por_materia: MateriaSummary[]
}

export interface MateriaSummary {
  materia_id: string
  materia_nombre: string
  atrasados: number
  al_dia: number
}

export interface MonitorFiltros {
  desde?: string
  hasta?: string
}

// ─── Encuentros Admin ─────────────────────────────────────────────────────────

export type EncuentroTipo = 'individual' | 'grupal'
export type EncuentroEstado = 'programado' | 'realizado' | 'cancelado' | 'ausente'
export type Recurrencia = 'semanal' | 'quincenal'

export interface EncuentroAdmin {
  id: string
  alumno_id: string
  alumno_nombre: string
  tutor_id: string
  tutor_nombre: string
  fecha: string
  hora: string
  tipo: EncuentroTipo
  estado: EncuentroEstado
  tenant_id: string
}

export interface SlotRecurrente {
  dia_semana: number // 0=lunes, 6=domingo
  hora: string
  recurrencia: Recurrencia
  periodo: string
  tutor_id: string
}

export interface UpdateEncuentroPayload {
  fecha?: string
  hora?: string
  estado?: EncuentroEstado
}

// ─── Coloquios ────────────────────────────────────────────────────────────────

export type ConvocatoriaEstado = 'abierta' | 'cerrada' | 'finalizada'

export interface Convocatoria {
  id: string
  materia_id: string
  materia_nombre: string
  fecha: string
  cupo: number
  inscriptos: number
  descripcion: string
  estado: ConvocatoriaEstado
  tenant_id: string
}

export interface ConvocatoriaMetrics {
  convocatoria_id: string
  aprobados: number
  desaprobados: number
  ausentes: number
  nota_promedio: number
}

export interface CreateConvocatoriaPayload {
  materia_id: string
  fecha: string
  cupo: number
  descripcion: string
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
