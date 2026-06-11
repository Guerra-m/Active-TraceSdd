import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { AtrasadosPage } from './AtrasadosPage'
import * as academicoService from '../services/academicoService'
import type { AtrasadosResponse, RankingResponse, NotasFinalesResponse } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const ATRASADOS_RESP: AtrasadosResponse = {
  total_atrasados: 1,
  alumnos: [
    { entrada_padron_id: 'ep1', nombre: 'Juan', apellidos: 'Pérez', faltantes: ['TP1'], reprobadas: [] },
  ],
}

const RANKING_RESP: RankingResponse = {
  total_alumnos: 1,
  ranking: [
    { posicion: 1, entrada_padron_id: 'ep2', nombre: 'Ana', apellidos: 'López', aprobadas: 5, total: 6 },
  ],
}

const NOTAS_RESP: NotasFinalesResponse = {
  total_alumnos: 1,
  alumnos: [
    { entrada_padron_id: 'ep1', nombre: 'Juan', apellidos: 'Pérez', promedio_numerico: 7.0, aprobadas: 3, total: 4 },
  ],
}

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchAtrasados').mockResolvedValue(ATRASADOS_RESP)
  vi.spyOn(academicoService, 'fetchRanking').mockResolvedValue(RANKING_RESP)
  vi.spyOn(academicoService, 'fetchNotasFinales').mockResolvedValue(NOTAS_RESP)
})

describe('AtrasadosPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<AtrasadosPage asignacionId="a1" materiaId="m1" />)
    expect(screen.getByText('Alumnos atrasados')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay asignación seleccionada', () => {
    wrapper(<AtrasadosPage asignacionId="" materiaId="" />)
    expect(screen.getByText('No hay asignación seleccionada.')).toBeInTheDocument()
  })

  it('muestra alumnos atrasados cargados desde la API', async () => {
    wrapper(<AtrasadosPage asignacionId="a1" materiaId="m1" />)
    const apellidos = await screen.findAllByText('Pérez')
    expect(apellidos.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('TP1')).toBeInTheDocument()
  })

  it('muestra mensaje vacío cuando no hay atrasados', async () => {
    vi.spyOn(academicoService, 'fetchAtrasados').mockResolvedValue({ total_atrasados: 0, alumnos: [] })
    wrapper(<AtrasadosPage asignacionId="a1" materiaId="m1" />)
    const msg = await screen.findByText('No hay alumnos atrasados en esta comisión')
    expect(msg).toBeInTheDocument()
  })

  it('muestra sección de ranking con datos', async () => {
    wrapper(<AtrasadosPage asignacionId="a1" materiaId="m1" />)
    expect(await screen.findByText('López')).toBeInTheDocument()
  })

  it('muestra sección de notas finales con datos', async () => {
    wrapper(<AtrasadosPage asignacionId="a1" materiaId="m1" />)
    expect(await screen.findByText('7')).toBeInTheDocument()
  })
})
