import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ComunicacionesPage } from './ComunicacionesPage'
import * as academicoService from '../services/academicoService'
import type { ComunicacionResponse, ComunicacionEstado } from '../types'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const RESPONSE: ComunicacionResponse = { id: 'com1', estado: 'PENDIENTE', mensaje: 'Comunicación creada' }
const ESTADO_FINAL: ComunicacionEstado = { id: 'com1', estado: 'ENVIADO', enviado_at: '2024-06-11T10:00:00Z' }

beforeEach(() => {
  vi.spyOn(academicoService, 'postComunicacion').mockResolvedValue(RESPONSE)
  vi.spyOn(academicoService, 'fetchEstadoComunicacion').mockResolvedValue(ESTADO_FINAL)
})

describe('ComunicacionesPage', () => {
  it('muestra el título de la página', () => {
    wrapper(<ComunicacionesPage comisionId="c1" />)
    expect(screen.getByText('Comunicaciones a atrasados')).toBeInTheDocument()
  })

  it('renderiza el formulario con campos asunto y cuerpo', () => {
    wrapper(<ComunicacionesPage comisionId="c1" />)
    expect(screen.getByLabelText('Asunto')).toBeInTheDocument()
    expect(screen.getByLabelText('Mensaje')).toBeInTheDocument()
  })

  it('muestra preview del mensaje antes de enviar', async () => {
    const user = userEvent.setup()
    wrapper(<ComunicacionesPage comisionId="c1" />)
    await user.type(screen.getByLabelText('Asunto'), 'Recordatorio')
    await user.type(screen.getByLabelText('Mensaje'), 'Tenés materias atrasadas')
    await user.click(screen.getByRole('button', { name: /ver preview/i }))
    expect(await screen.findByText('Recordatorio')).toBeInTheDocument()
    expect(screen.getByText('Tenés materias atrasadas')).toBeInTheDocument()
  })

  it('cancela el preview y vuelve al formulario', async () => {
    const user = userEvent.setup()
    wrapper(<ComunicacionesPage comisionId="c1" />)
    await user.type(screen.getByLabelText('Asunto'), 'Test')
    await user.type(screen.getByLabelText('Mensaje'), 'Cuerpo')
    await user.click(screen.getByRole('button', { name: /ver preview/i }))
    await screen.findByText('Test')
    await user.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(screen.getByLabelText('Asunto')).toBeInTheDocument()
  })

  it('envía la comunicación y muestra tracking', async () => {
    const user = userEvent.setup()
    wrapper(<ComunicacionesPage comisionId="c1" />)
    await user.type(screen.getByLabelText('Asunto'), 'Recordatorio')
    await user.type(screen.getByLabelText('Mensaje'), 'Tenés materias atrasadas')
    await user.click(screen.getByRole('button', { name: /ver preview/i }))
    await screen.findByText('Recordatorio')
    await user.click(screen.getByRole('button', { name: /confirmar envío/i }))
    await waitFor(() => {
      expect(screen.getByText('ENVIADO')).toBeInTheDocument()
    })
  })

  it('muestra error de validación si asunto está vacío', async () => {
    const user = userEvent.setup()
    wrapper(<ComunicacionesPage comisionId="c1" />)
    // Solo llenamos el cuerpo, no el asunto
    await user.type(screen.getByLabelText('Mensaje'), 'Contenido')
    fireEvent.click(screen.getByRole('button', { name: /ver preview/i }))
    expect(await screen.findByText(/asunto es obligatorio/i)).toBeInTheDocument()
  })
})
