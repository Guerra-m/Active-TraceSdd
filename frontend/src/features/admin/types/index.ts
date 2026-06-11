// ─── Estructura académica ─────────────────────────────────────────────────────

export interface Carrera {
  id: string
  nombre: string
  codigo: string
  activa: boolean
  tenant_id: string
}

export interface CreateCarreraPayload {
  nombre: string
  codigo: string
  activa?: boolean
}

export interface UpdateCarreraPayload {
  nombre?: string
  codigo?: string
  activa?: boolean
}

export interface Cohorte {
  id: string
  carrera_id: string
  carrera_nombre: string
  anio: number
  periodo: string
  activa: boolean
  tenant_id: string
}

export interface CreateCohortePayload {
  carrera_id: string
  anio: number
  periodo: string
  activa?: boolean
}

export interface UpdateCohortePayload {
  carrera_id?: string
  anio?: number
  periodo?: string
  activa?: boolean
}

export interface Materia {
  id: string
  nombre: string
  codigo: string
  carrera_id: string
  carrera_nombre: string
  grupo_plus: string | null
  activa: boolean
  tenant_id: string
}

export interface CreateMateriaPayload {
  nombre: string
  codigo: string
  carrera_id: string
  grupo_plus?: string
  activa?: boolean
}

export interface UpdateMateriaPayload {
  nombre?: string
  codigo?: string
  carrera_id?: string
  grupo_plus?: string | null
  activa?: boolean
}

// ─── Usuarios Admin ───────────────────────────────────────────────────────────

export type RolUsuario = 'ALUMNO' | 'TUTOR' | 'PROFESOR' | 'COORDINADOR' | 'NEXO' | 'ADMIN' | 'FINANZAS'

export interface UsuarioAdmin {
  id: string
  email: string
  nombre: string
  rol: RolUsuario
  activo: boolean
  tenant_id: string
}

export interface UpdateUsuarioAdminPayload {
  activo?: boolean
  rol?: RolUsuario
}

// ─── Auditoría ────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string
  usuario_id: string
  usuario_nombre: string
  accion: string
  recurso: string
  recurso_id: string | null
  detalle: Record<string, unknown>
  ip: string | null
  creado_en: string
  tenant_id: string
}

export interface AuditLogFiltros {
  desde?: string
  hasta?: string
  materia_id?: string
  usuario_id?: string
  accion?: string
  page?: number
  page_size?: number
}

export interface AuditPanel {
  acciones_por_dia: { fecha: string; count: number }[]
  comunicaciones_por_docente: { docente_nombre: string; enviadas: number; fallidas: number }[]
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
