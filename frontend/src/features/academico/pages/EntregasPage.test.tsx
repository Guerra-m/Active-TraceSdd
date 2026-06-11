import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { EntregasPage } from './EntregasPage'
import * as academicoService from '../services/academicoService'
import type { EntregasSinCorregirResponse } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const RESP: EntregasSinCorregirResponse = {
  total: 2,
  items: [
    { entrada_padron_id: 'ep1', nombre: 'Pedro', apellidos: 'García', actividad: 'TP 1', importado_at: '2024-05-20T00:00:00Z' },
    { entrada_padron_id: 'ep2', nombre: 'Laura', apellidos: 'Díaz', actividad: 'TP 2', importado_at: '2024-06-01T00:00:00Z' },
  ],
}

const RESP_VACIO: EntregasSinCorregirResponse = { total: 0, items: [] }

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue(RESP)
})

describe('EntregasPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    expect(screen.getByText('Entregas sin corregir')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay asignación seleccionada', () => {
    wrapper(<EntregasPage asignacionId="" materiaId="" />)
    expect(screen.getByText('No hay asignación seleccionada.')).toBeInTheDocument()
  })

  it('muestra las entregas cargadas', async () => {
    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    expect(await screen.findByText('García')).toBeInTheDocument()
    expect(screen.getByText('Díaz')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay entregas pendientes', async () => {
    vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue(RESP_VACIO)
    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    expect(await screen.findByText('No hay entregas pendientes de corrección')).toBeInTheDocument()
  })

  it('el botón exportar CSV está habilitado cuando hay entregas', async () => {
    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    await screen.findByText('García')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    expect(btn).not.toBeDisabled()
  })

  it('el botón exportar CSV está deshabilitado cuando no hay entregas', async () => {
    vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue(RESP_VACIO)
    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    await screen.findByText('No hay entregas pendientes de corrección')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    expect(btn).toBeDisabled()
  })

  it('dispara la descarga al hacer clic en exportar', async () => {
    const createObjectURL = vi.fn(() => 'blob:url')
    const revokeObjectURL = vi.fn()
    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = revokeObjectURL

    wrapper(<EntregasPage asignacionId="a1" materiaId="m1" />)
    await screen.findByText('García')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    fireEvent.click(btn)
    expect(createObjectURL).toHaveBeenCalled()
  })
})
