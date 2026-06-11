import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { MonitorPage } from './MonitorPage'
import * as academicoService from '../services/academicoService'
import type { MonitorData } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const MONITOR: MonitorData = {
  total_alumnos: 30,
  atrasados: 5,
  al_dia: 25,
  promedio_general: 7.4,
  comunicaciones_enviadas: 3,
  comunicaciones_pendientes: 1,
}

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchMonitor').mockResolvedValue(MONITOR)
})

describe('MonitorPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<MonitorPage comisionId="c1" />)
    expect(screen.getByText('Monitor de seguimiento')).toBeInTheDocument()
  })

  it('muestra las métricas de la comisión', async () => {
    wrapper(<MonitorPage comisionId="c1" />)
    expect(await screen.findByText('30')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
  })

  it('muestra el promedio general', async () => {
    wrapper(<MonitorPage comisionId="c1" />)
    expect(await screen.findByText('7.4')).toBeInTheDocument()
  })

  it('muestra contadores de comunicaciones', async () => {
    wrapper(<MonitorPage comisionId="c1" />)
    expect(await screen.findByText('3')).toBeInTheDocument()
  })

  it('muestra error cuando la carga falla', async () => {
    vi.spyOn(academicoService, 'fetchMonitor').mockRejectedValue(new Error('Network error'))
    wrapper(<MonitorPage comisionId="c1" />)
    expect(await screen.findByText(/error al cargar/i)).toBeInTheDocument()
  })
})
