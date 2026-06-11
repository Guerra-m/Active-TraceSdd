import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { EntregasPage } from './EntregasPage'
import * as academicoService from '../services/academicoService'
import type { EntregaSinCorregir } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const ENTREGAS: EntregaSinCorregir[] = [
  { id: 'e1', alumno_nombre: 'Pedro García', alumno_legajo: 'L010', actividad: 'TP 1', fecha_entrega: '2024-05-20', estado: 'pendiente' },
  { id: 'e2', alumno_nombre: 'Laura Díaz', alumno_legajo: 'L011', actividad: 'TP 2', fecha_entrega: '2024-06-01', estado: 'pendiente' },
]

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue(ENTREGAS)
})

describe('EntregasPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<EntregasPage comisionId="c1" />)
    expect(screen.getByText('Entregas sin corregir')).toBeInTheDocument()
  })

  it('muestra las entregas cargadas', async () => {
    wrapper(<EntregasPage comisionId="c1" />)
    expect(await screen.findByText('Pedro García')).toBeInTheDocument()
    expect(screen.getByText('Laura Díaz')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay entregas pendientes', async () => {
    vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue([])
    wrapper(<EntregasPage comisionId="c1" />)
    expect(await screen.findByText('No hay entregas pendientes de corrección')).toBeInTheDocument()
  })

  it('el botón exportar CSV está habilitado cuando hay entregas', async () => {
    wrapper(<EntregasPage comisionId="c1" />)
    await screen.findByText('Pedro García')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    expect(btn).not.toBeDisabled()
  })

  it('el botón exportar CSV está deshabilitado cuando no hay entregas', async () => {
    vi.spyOn(academicoService, 'fetchEntregasSinCorregir').mockResolvedValue([])
    wrapper(<EntregasPage comisionId="c1" />)
    await screen.findByText('No hay entregas pendientes de corrección')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    expect(btn).toBeDisabled()
  })

  it('dispara la descarga al hacer clic en exportar', async () => {
    const createObjectURL = vi.fn(() => 'blob:url')
    const revokeObjectURL = vi.fn()
    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = revokeObjectURL

    wrapper(<EntregasPage comisionId="c1" />)
    await screen.findByText('Pedro García')
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    fireEvent.click(btn)
    expect(createObjectURL).toHaveBeenCalled()
  })
})
