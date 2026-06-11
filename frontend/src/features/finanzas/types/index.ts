// ─── Liquidaciones ────────────────────────────────────────────────────────────

export type LiquidacionEstado = 'Abierta' | 'Cerrada'

export interface Liquidacion {
  id: string
  tenant_id: string
  cohorte_id: string
  periodo: string
  usuario_id: string
  rol: string
  comisiones: string[]
  monto_base: number
  monto_plus: number
  total: number
  es_nexo: boolean
  excluido_por_factura: boolean
  estado: LiquidacionEstado
  created_at: string
  updated_at: string
}

export interface LiquidacionKPIs {
  periodo: string
  cohorte_id: string
  total_general: number
  total_nexo: number
  total_facturantes: number
  cantidad_liquidaciones: number
}

export interface CalcularLiquidacionPayload {
  cohorte_id: string
  periodo: string // YYYY-MM
}

export interface LiquidacionFiltros {
  cohorte_id?: string
  periodo?: string
}

// ─── Salarios ────────────────────────────────────────────────────────────────

export interface SalarioBase {
  id: string
  rol: string
  monto: number
  desde: string
  hasta: string | null
  tenant_id: string
}

export interface SalarioPlus {
  id: string
  rol: string
  monto: number
  desde: string
  hasta: string | null
  tenant_id: string
}

export interface CreateSalarioBasePayload {
  rol: string
  monto: number
  desde: string
  hasta?: string
}

export interface UpdateSalarioBasePayload {
  rol?: string
  monto?: number
  desde?: string
  hasta?: string | null
}

export interface CreateSalarioPlusPayload {
  rol: string
  monto: number
  desde: string
  hasta?: string
}

export interface UpdateSalarioPlusPayload {
  rol?: string
  monto?: number
  desde?: string
  hasta?: string | null
}

// ─── Facturas ────────────────────────────────────────────────────────────────

export type FacturaEstado = 'Pendiente' | 'Abonada'

export interface Factura {
  id: string
  tenant_id: string
  usuario_id: string
  periodo: string
  monto: number
  detalle: string
  archivo_ref: string | null
  estado: FacturaEstado
  fecha_carga: string
  fecha_pago: string | null
  created_at: string
  updated_at: string
}

export interface CreateFacturaPayload {
  usuario_id: string
  monto: number
  periodo: string
  detalle?: string
  archivo_ref?: string
}

export interface FacturaFiltros {
  usuario_id?: string
  periodo?: string
  estado?: FacturaEstado
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
