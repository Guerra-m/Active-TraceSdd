import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { UmbralPage } from './UmbralPage'
import * as academicoService from '../services/academicoService'
import type { UmbralResponse } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const UMBRAL_ACTUAL: UmbralResponse = {
  umbral_pct: 60,
  valores_aprobatorios: ['Satisfactorio', 'Supera lo esperado'],
  es_default: false,
}

const UMBRAL_ACTUALIZADO: UmbralResponse = {
  umbral_pct: 75,
  valores_aprobatorios: ['Satisfactorio', 'Supera lo esperado'],
  es_default: false,
}

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchUmbral').mockResolvedValue(UMBRAL_ACTUAL)
  vi.spyOn(academicoService, 'putUmbral').mockResolvedValue(UMBRAL_ACTUALIZADO)
})

describe('UmbralPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<UmbralPage asignacionId="a1" materiaId="m1" />)
    expect(screen.getByText('Configuración de umbral')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay asignación seleccionada', () => {
    wrapper(<UmbralPage asignacionId="" materiaId="" />)
    expect(screen.getByText('No hay asignación seleccionada.')).toBeInTheDocument()
  })

  it('muestra el valor actual del umbral', async () => {
    wrapper(<UmbralPage asignacionId="a1" materiaId="m1" />)
    const input = await screen.findByRole('spinbutton')
    expect(input).toHaveValue(60)
  })

  it('muestra error de validación con valor fuera de rango', async () => {
    wrapper(<UmbralPage asignacionId="a1" materiaId="m1" />)
    const input = await screen.findByRole('spinbutton')
    fireEvent.change(input, { target: { value: '150' } })
    const btn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(btn)
    expect(await screen.findByText(/entre 1 y 100/i)).toBeInTheDocument()
  })

  it('guarda el umbral y muestra éxito', async () => {
    wrapper(<UmbralPage asignacionId="a1" materiaId="m1" />)
    const input = await screen.findByRole('spinbutton')
    fireEvent.change(input, { target: { value: '75' } })
    const btn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText(/guardado/i)).toBeInTheDocument()
    })
  })
})
