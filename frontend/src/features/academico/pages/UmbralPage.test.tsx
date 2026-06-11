import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { UmbralPage } from './UmbralPage'
import * as academicoService from '../services/academicoService'
import type { Umbral } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const UMBRAL_ACTUAL: Umbral = { id: 'u1', comision_id: 'c1', porcentaje: 60 }

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchUmbral').mockResolvedValue(UMBRAL_ACTUAL)
  vi.spyOn(academicoService, 'putUmbral').mockResolvedValue({ ...UMBRAL_ACTUAL, porcentaje: 75 })
})

describe('UmbralPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<UmbralPage comisionId="c1" />)
    expect(screen.getByText('Configuración de umbral')).toBeInTheDocument()
  })

  it('muestra el valor actual del umbral', async () => {
    wrapper(<UmbralPage comisionId="c1" />)
    const input = await screen.findByRole('spinbutton')
    expect(input).toHaveValue(60)
  })

  it('muestra error de validación con valor fuera de rango', async () => {
    wrapper(<UmbralPage comisionId="c1" />)
    const input = await screen.findByRole('spinbutton')
    fireEvent.change(input, { target: { value: '150' } })
    const btn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(btn)
    expect(await screen.findByText(/entre 0 y 100/i)).toBeInTheDocument()
  })

  it('guarda el umbral y muestra éxito', async () => {
    wrapper(<UmbralPage comisionId="c1" />)
    const input = await screen.findByRole('spinbutton')
    fireEvent.change(input, { target: { value: '75' } })
    const btn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText(/guardado/i)).toBeInTheDocument()
    })
  })
})
