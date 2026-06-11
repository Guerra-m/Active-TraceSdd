// ─── Atrasados ────────────────────────────────────────────────────────────────

export interface AlumnoAtrasado {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  faltantes: string[]
  reprobadas: string[]
}

export interface AtrasadosResponse {
  total_atrasados: number
  alumnos: AlumnoAtrasado[]
}

// ─── Ranking ─────────────────────────────────────────────────────────────────

export interface AlumnoRanking {
  posicion: number
  entrada_padron_id: string
  nombre: string
  apellidos: string
  aprobadas: number
  total: number
}

export interface RankingResponse {
  total_alumnos: number
  ranking: AlumnoRanking[]
}

// ─── Notas finales ────────────────────────────────────────────────────────────

export interface AlumnoNotaFinal {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  promedio_numerico: number | null
  aprobadas: number
  total: number
}

export interface NotasFinalesResponse {
  total_alumnos: number
  alumnos: AlumnoNotaFinal[]
}

// ─── Umbral ───────────────────────────────────────────────────────────────────

export interface UmbralResponse {
  umbral_pct: number
  valores_aprobatorios: string[]
  es_default: boolean
}

export interface UmbralPayload {
  umbral_pct: number
  valores_aprobatorios?: string[]
}

// ─── Importación ──────────────────────────────────────────────────────────────

export interface ImportarCalificacionesResponse {
  asignacion_id: string
  materia_id: string
  filas_importadas: number
  actividades_detectadas: string[]
}

// ─── Entregas sin corregir ────────────────────────────────────────────────────

export interface EntregaSinCorregir {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  actividad: string
  importado_at: string
}

export interface EntregasSinCorregirResponse {
  total: number
  items: EntregaSinCorregir[]
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export type EstadoLote =
  | 'Pendiente'
  | 'PendienteAprobacion'
  | 'Aprobado'
  | 'Despachando'
  | 'Completado'
  | 'Cancelado'

export interface ComunicacionPorCriterioPayload {
  asignacion_id: string
  materia_id: string
  criterio: 'atrasados' | 'todos'
  asunto_template: string
  cuerpo_template: string
}

export interface LoteComunicacionResponse {
  id: string
  estado: EstadoLote
  requiere_aprobacion: boolean
  total_mensajes: number
  enviados: number
  errores: number
  materia_id: string | null
  aprobado_at: string | null
  created_at: string
}

// ─── Monitor ─────────────────────────────────────────────────────────────────

export interface MonitorData {
  total_alumnos: number
  atrasados: number
  al_dia: number
  promedio_general: number | null
  comunicaciones_enviadas: number
  comunicaciones_pendientes: number
}
