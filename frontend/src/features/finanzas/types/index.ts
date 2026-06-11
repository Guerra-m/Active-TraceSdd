// ─── Liquidaciones ────────────────────────────────────────────────────────────

export type LiquidacionEstado = 'borrador' | 'cerrada' | 'anulada'
export type TipoDocente = 'general' | 'nexo' | 'facturante'

export interface Liquidacion {
  id: string
  docente_id: string
  docente_nombre: string
  tipo: TipoDocente
  cohorte_id: string
  periodo: string // YYYY-MM
  monto_base: number
  monto_plus: number
  monto_total: number
  estado: LiquidacionEstado
  tenant_id: string
}

export interface LiquidacionKPIs {
  total_general: number
  total_nexo: number
  total_facturantes: number
  count_general: number
  count_nexo: number
  count_facturantes: number
}

export interface CalcularLiquidacionPayload {
  cohorte_id: string
  periodo: string // YYYY-MM
}

export interface LiquidacionPreview {
  items: Liquidacion[]
  kpis: LiquidacionKPIs
}

export interface LiquidacionFiltros {
  cohorte_id?: string
  periodo?: string
  estado?: LiquidacionEstado
  page?: number
  page_size?: number
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

export type FacturaEstado = 'pendiente' | 'abonada' | 'anulada'

export interface Factura {
  id: string
  docente_id: string
  docente_nombre: string
  monto: number
  periodo: string
  numero_factura: string
  estado: FacturaEstado
  fecha_emision: string
  fecha_pago: string | null
  tenant_id: string
}

export interface CreateFacturaPayload {
  docente_id: string
  monto: number
  periodo: string
  numero_factura: string
  fecha_emision: string
}

export interface FacturaFiltros {
  docente_id?: string
  periodo?: string
  estado?: FacturaEstado
  page?: number
  page_size?: number
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
