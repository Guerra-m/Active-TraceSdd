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

export interface UsuarioAdmin {
  id: string
  tenant_id: string
  nombre: string | null
  apellidos: string | null
  legajo: string | null
  estado: string
  is_active: boolean
  facturador: boolean
  created_at: string
  updated_at: string
}

export interface UpdateUsuarioAdminPayload {
  estado?: string
  nombre?: string
  apellidos?: string
}

// ─── Auditoría ────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string
  tenant_id: string
  fecha_hora: string
  actor_id: string
  impersonado_id: string | null
  materia_id: string | null
  accion: string
  detalle: Record<string, unknown> | null
  filas_afectadas: number | null
  ip: string | null
  user_agent: string | null
}

export interface AuditLogFiltros {
  actor_id?: string
  materia_id?: string
  accion?: string
  fecha_desde?: string
  fecha_hasta?: string
  limit?: number
}

export interface MetricasAuditoria {
  acciones_por_dia: { fecha: string; total: number }[]
  por_actor: { actor_id: string; materia_id: string | null; total: number }[]
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
