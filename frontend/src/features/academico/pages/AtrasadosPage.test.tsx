import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { AtrasadosPage } from './AtrasadosPage'
import * as academicoService from '../services/academicoService'
import type { AlumnoAtrasado, AlumnoRanking, AlumnoNotaFinal } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const ATRASADOS: AlumnoAtrasado[] = [
  { id: '1', nombre: 'Juan Pérez', legajo: 'L001', entregas_atrasadas: 3, ultimo_atraso: '2024-06-01' },
]

const RANKING: AlumnoRanking[] = [
  { posicion: 1, nombre: 'Ana López', legajo: 'L002', promedio: 9.5 },
]

const NOTAS: AlumnoNotaFinal[] = [
  { id: '1', nombre: 'Juan Pérez', legajo: 'L001', nota_final: 7.0 },
]

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchAtrasados').mockResolvedValue(ATRASADOS)
  vi.spyOn(academicoService, 'fetchRanking').mockResolvedValue(RANKING)
  vi.spyOn(academicoService, 'fetchNotasFinales').mockResolvedValue(NOTAS)
})

describe('AtrasadosPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<AtrasadosPage comisionId="c1" />)
    expect(screen.getByText('Alumnos atrasados')).toBeInTheDocument()
  })

  it('muestra alumnos atrasados cargados desde la API', async () => {
    wrapper(<AtrasadosPage comisionId="c1" />)
    // Juan Pérez aparece en atrasados Y notas finales — usamos findAllByText
    const nombres = await screen.findAllByText('Juan Pérez')
    expect(nombres.length).toBeGreaterThanOrEqual(1)
    // Verificar que aparece la columna entregas_atrasadas (solo en la tabla de atrasados)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('muestra mensaje vacío cuando no hay atrasados', async () => {
    vi.spyOn(academicoService, 'fetchAtrasados').mockResolvedValue([])
    wrapper(<AtrasadosPage comisionId="c1" />)
    const msg = await screen.findByText('No hay alumnos atrasados en esta comisión')
    expect(msg).toBeInTheDocument()
  })

  it('muestra sección de ranking con datos', async () => {
    wrapper(<AtrasadosPage comisionId="c1" />)
    expect(await screen.findByText('Ana López')).toBeInTheDocument()
  })

  it('muestra sección de notas finales con datos', async () => {
    wrapper(<AtrasadosPage comisionId="c1" />)
    expect(await screen.findByText('7')).toBeInTheDocument()
  })
})
