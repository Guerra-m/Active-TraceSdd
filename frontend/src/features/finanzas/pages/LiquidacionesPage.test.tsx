import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { LiquidacionesPage } from './LiquidacionesPage'
import * as liquidacionesService from '../services/liquidacionesService'
import type { Liquidacion, LiquidacionKPIs } from '../types'

// Mock RequirePermission to always render children in tests
vi.mock('@/shared/components/RequirePermission', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockLiquidaciones: Liquidacion[] = [
  {
    id: 'liq-1',
    tenant_id: 'tenant-1',
    cohorte_id: 'coh-1',
    periodo: '2024-03',
    usuario_id: 'usr-abc12345',
    rol: 'PROFESOR',
    comisiones: [],
    monto_base: 100000,
    monto_plus: 20000,
    total: 120000,
    es_nexo: false,
    excluido_por_factura: false,
    estado: 'Abierta',
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
  },
  {
    id: 'liq-2',
    tenant_id: 'tenant-1',
    cohorte_id: 'coh-1',
    periodo: '2024-03',
    usuario_id: 'usr-def67890',
    rol: 'TUTOR',
    comisiones: [],
    monto_base: 150000,
    monto_plus: 50000,
    total: 200000,
    es_nexo: true,
    excluido_por_factura: false,
    estado: 'Cerrada',
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
  },
]

const mockKPIs: LiquidacionKPIs = {
  periodo: '2024-03',
  cohorte_id: 'coh-1',
  total_general: 120000,
  total_nexo: 200000,
  total_facturantes: 0,
  cantidad_liquidaciones: 2,
}

describe('LiquidacionesPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra spinner mientras carga', () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockReturnValue(new Promise(() => {}))
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockReturnValue(new Promise(() => {}))

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    expect(document.querySelector('[role="status"]') ?? document.querySelector('svg')).toBeTruthy()
  })

  it('muestra la lista de liquidaciones tras cargar', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockResolvedValue(mockLiquidaciones)
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('usr-abc1')).toBeInTheDocument()
    })

    expect(screen.getByText('usr-def6')).toBeInTheDocument()
  })

  it('muestra KPIs cuando están disponibles', async () => {
    const user = userEvent.setup()
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockResolvedValue(mockLiquidaciones)
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    // Esperar que cargue la lista antes de interactuar con el formulario
    await waitFor(() => screen.getByPlaceholderText('UUID cohorte'))

    // Cargar KPIs requiere cohorte_id además del período
    const cohorteInput = screen.getByPlaceholderText('UUID cohorte')
    await user.clear(cohorteInput)
    await user.type(cohorteInput, 'coh-1')
    await user.click(screen.getByRole('button', { name: /filtrar/i }))

    await waitFor(() => {
      expect(screen.getByText(/Facturantes \(2\)/)).toBeInTheDocument()
    })

    expect(screen.getAllByText('NEXO').length).toBeGreaterThan(0)
  })

  it('muestra mensaje de error cuando falla la carga', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockRejectedValue(
      new Error('Network error'),
    )
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('muestra botón "Calcular liquidación"', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockResolvedValue(mockLiquidaciones)
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Calcular liquidación')).toBeInTheDocument()
    })
  })
})
