import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { LiquidacionesPage } from './LiquidacionesPage'
import * as liquidacionesService from '../services/liquidacionesService'
import type { PagedResponse, Liquidacion, LiquidacionKPIs } from '../types'

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

const mockLiquidaciones: PagedResponse<Liquidacion> = {
  items: [
    {
      id: 'liq-1',
      docente_id: 'doc-1',
      docente_nombre: 'Juan Pérez',
      tipo: 'general',
      cohorte_id: 'coh-1',
      periodo: '2024-03',
      monto_base: 100000,
      monto_plus: 20000,
      monto_total: 120000,
      estado: 'borrador',
      tenant_id: 'tenant-1',
    },
    {
      id: 'liq-2',
      docente_id: 'doc-2',
      docente_nombre: 'Ana López',
      tipo: 'nexo',
      cohorte_id: 'coh-1',
      periodo: '2024-03',
      monto_base: 150000,
      monto_plus: 50000,
      monto_total: 200000,
      estado: 'cerrada',
      tenant_id: 'tenant-1',
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
}

const mockKPIs: LiquidacionKPIs = {
  total_general: 120000,
  total_nexo: 200000,
  total_facturantes: 0,
  count_general: 1,
  count_nexo: 1,
  count_facturantes: 0,
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
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    })

    expect(screen.getByText('Ana López')).toBeInTheDocument()
  })

  it('muestra KPIs cuando están disponibles', async () => {
    vi.spyOn(liquidacionesService, 'fetchLiquidaciones').mockResolvedValue(mockLiquidaciones)
    vi.spyOn(liquidacionesService, 'fetchLiquidacionKPIs').mockResolvedValue(mockKPIs)

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/General \(1\)/)).toBeInTheDocument()
    })

    expect(screen.getByText(/NEXO \(1\)/)).toBeInTheDocument()
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
