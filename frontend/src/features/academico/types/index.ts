// ─── Calificaciones / Importación ────────────────────────────────────────────

export interface ActividadPreview {
  id: string
  nombre: string
  tipo: string
  fecha: string
}

export interface ImportacionPayload {
  comision_id: string
  actividad_ids: string[]
}

export interface ImportacionResult {
  importadas: number
  mensaje: string
}

// ─── Umbral ───────────────────────────────────────────────────────────────────

export interface Umbral {
  id: string
  comision_id: string
  porcentaje: number
}

export interface UmbralPayload {
  porcentaje: number
}

// ─── Atrasados ────────────────────────────────────────────────────────────────

export interface AlumnoAtrasado {
  id: string
  nombre: string
  legajo: string
  entregas_atrasadas: number
  ultimo_atraso: string
}

export interface AlumnoRanking {
  posicion: number
  nombre: string
  legajo: string
  promedio: number
}

export interface AlumnoNotaFinal {
  id: string
  nombre: string
  legajo: string
  nota_final: number | null
}

// ─── Entregas sin corregir ────────────────────────────────────────────────────

export interface EntregaSinCorregir {
  id: string
  alumno_nombre: string
  alumno_legajo: string
  actividad: string
  fecha_entrega: string
  estado: string
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export type EstadoComunicacion = 'PENDIENTE' | 'ENVIANDO' | 'ENVIADO' | 'FALLIDO' | 'CANCELADO'

export interface ComunicacionPayload {
  comision_id: string
  asunto: string
  cuerpo: string
  destinatarios: 'atrasados' | 'todos'
}

export interface ComunicacionResponse {
  id: string
  estado: EstadoComunicacion
  mensaje: string
}

export interface ComunicacionEstado {
  id: string
  estado: EstadoComunicacion
  motivo_fallo?: string
  enviado_at?: string
}

// ─── Monitor ─────────────────────────────────────────────────────────────────

export interface MonitorData {
  total_alumnos: number
  atrasados: number
  al_dia: number
  promedio_general: number
  comunicaciones_enviadas: number
  comunicaciones_pendientes: number
}
