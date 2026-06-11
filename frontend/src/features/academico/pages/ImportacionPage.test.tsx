import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ImportacionPage } from './ImportacionPage'
import * as academicoService from '../services/academicoService'
import type { ActividadPreview, ImportacionResult } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const ACTIVIDADES: ActividadPreview[] = [
  { id: 'a1', nombre: 'Parcial 1', tipo: 'examen', fecha: '2024-05-01' },
  { id: 'a2', nombre: 'TP Final', tipo: 'trabajo', fecha: '2024-06-15' },
]

const RESULTADO: ImportacionResult = { importadas: 2, mensaje: 'Importación exitosa' }

beforeEach(() => {
  vi.spyOn(academicoService, 'fetchPreviewCalificaciones').mockResolvedValue(ACTIVIDADES)
  vi.spyOn(academicoService, 'postImportarCalificaciones').mockResolvedValue(RESULTADO)
})

describe('ImportacionPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<ImportacionPage comisionId="c1" />)
    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument()
  })

  it('muestra lista de actividades del preview', async () => {
    wrapper(<ImportacionPage comisionId="c1" />)
    expect(await screen.findByText('Parcial 1')).toBeInTheDocument()
    expect(screen.getByText('TP Final')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay actividades disponibles', async () => {
    vi.spyOn(academicoService, 'fetchPreviewCalificaciones').mockResolvedValue([])
    wrapper(<ImportacionPage comisionId="c1" />)
    expect(await screen.findByText('No hay actividades disponibles para importar')).toBeInTheDocument()
  })

  it('bloquea el submit sin selección mostrando error', async () => {
    wrapper(<ImportacionPage comisionId="c1" />)
    await screen.findByText('Parcial 1')
    const btn = screen.getByRole('button', { name: /importar/i })
    fireEvent.click(btn)
    expect(await screen.findByText('Seleccioná al menos una actividad')).toBeInTheDocument()
  })

  it('importa actividades seleccionadas y muestra éxito', async () => {
    wrapper(<ImportacionPage comisionId="c1" />)
    const checkbox = await screen.findByLabelText('Parcial 1')
    fireEvent.click(checkbox)
    const btn = screen.getByRole('button', { name: /importar/i })
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText('Importación exitosa')).toBeInTheDocument()
    })
  })
})
