import { api } from '@/shared/services/api'
import type {
  Carrera,
  CreateCarreraPayload,
  UpdateCarreraPayload,
  SetEstadoCarreraPayload,
  Cohorte,
  CreateCohortePayload,
  Materia,
  CreateMateriaPayload,
  UpdateMateriaPayload,
  SetEstadoMateriaPayload,
} from '../types'

// ─── Carreras ─────────────────────────────────────────────────────────────────

export async function fetchCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[]>('/admin/carreras')
  return data
}

export async function createCarrera(payload: CreateCarreraPayload): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/admin/carreras', payload)
  return data
}

export async function updateCarrera(id: string, payload: UpdateCarreraPayload): Promise<Carrera> {
  const { data } = await api.put<Carrera>(`/admin/carreras/${id}`, payload)
  return data
}

export async function patchCarreraEstado(id: string, payload: SetEstadoCarreraPayload): Promise<Carrera> {
  const { data } = await api.patch<Carrera>(`/admin/carreras/${id}/estado`, payload)
  return data
}

export async function deleteCarrera(id: string): Promise<void> {
  await api.delete(`/admin/carreras/${id}`)
}

// ─── Cohortes ─────────────────────────────────────────────────────────────────

export async function fetchCohortes(): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[]>('/admin/cohortes')
  return data
}

export async function createCohorte(payload: CreateCohortePayload): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/admin/cohortes', payload)
  return data
}

export async function deleteCohorte(id: string): Promise<void> {
  await api.delete(`/admin/cohortes/${id}`)
}

// ─── Materias ─────────────────────────────────────────────────────────────────

export async function fetchMaterias(): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/admin/materias')
  return data
}

export async function createMateria(payload: CreateMateriaPayload): Promise<Materia> {
  const { data } = await api.post<Materia>('/admin/materias', payload)
  return data
}

export async function updateMateria(id: string, payload: UpdateMateriaPayload): Promise<Materia> {
  const { data } = await api.put<Materia>(`/admin/materias/${id}`, payload)
  return data
}

export async function patchMateriaEstado(id: string, payload: SetEstadoMateriaPayload): Promise<Materia> {
  const { data } = await api.patch<Materia>(`/admin/materias/${id}/estado`, payload)
  return data
}

export async function deleteMateria(id: string): Promise<void> {
  await api.delete(`/admin/materias/${id}`)
}
