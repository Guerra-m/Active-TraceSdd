import { api } from '@/shared/services/api'
import type {
  Tarea,
  Comentario,
  CreateTareaPayload,
  CambiarEstadoPayload,
  CreateComentarioPayload,
} from '../types'

export async function fetchTareas(): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[]>('/tareas')
  return data
}

export async function createTarea(payload: CreateTareaPayload): Promise<Tarea> {
  const { data } = await api.post<Tarea>('/tareas', payload)
  return data
}

export async function cambiarEstadoTarea(
  id: string,
  payload: CambiarEstadoPayload,
): Promise<Tarea> {
  const { data } = await api.patch<Tarea>(`/tareas/${id}`, payload)
  return data
}

export async function fetchComentarios(tareaId: string): Promise<Comentario[]> {
  const { data } = await api.get<Comentario[]>(`/tareas/${tareaId}/comentarios`)
  return data
}

export async function createComentario(
  tareaId: string,
  payload: CreateComentarioPayload,
): Promise<Comentario> {
  const { data } = await api.post<Comentario>(`/tareas/${tareaId}/comentarios`, payload)
  return data
}
