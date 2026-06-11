import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ImportacionPage } from './ImportacionPage'
import * as academicoService from '../services/academicoService'
import type { ImportarCalificacionesResponse } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const RESULTADO: ImportarCalificacionesResponse = {
  asignacion_id: 'a1',
  materia_id: 'm1',
  filas_importadas: 15,
  actividades_detectadas: ['TP 1', 'Parcial 1'],
}

beforeEach(() => {
  vi.spyOn(academicoService, 'postImportarCalificaciones').mockResolvedValue(RESULTADO)
})

describe('ImportacionPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<ImportacionPage asignacionId="a1" materiaId="m1" />)
    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay asignación seleccionada', () => {
    wrapper(<ImportacionPage asignacionId="" materiaId="" />)
    expect(screen.getByText('No hay asignación seleccionada.')).toBeInTheDocument()
  })

  it('muestra el input de archivo', () => {
    wrapper(<ImportacionPage asignacionId="a1" materiaId="m1" />)
    expect(screen.getByLabelText('Archivo de calificaciones')).toBeInTheDocument()
  })

  it('bloquea el submit sin archivo y muestra error', async () => {
    wrapper(<ImportacionPage asignacionId="a1" materiaId="m1" />)
    const btn = screen.getByRole('button', { name: /importar/i })
    fireEvent.click(btn)
    expect(await screen.findByText('Seleccioná un archivo xlsx o csv')).toBeInTheDocument()
  })

  it('importa el archivo y muestra resultado exitoso', async () => {
    wrapper(<ImportacionPage asignacionId="a1" materiaId="m1" />)
    const input = screen.getByLabelText('Archivo de calificaciones')
    const file = new File(['data'], 'notas.xlsx', { type: 'application/vnd.ms-excel' })
    fireEvent.change(input, { target: { files: [file] } })
    const btn = screen.getByRole('button', { name: /importar/i })
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText(/15 filas procesadas/i)).toBeInTheDocument()
    })
  })
})
