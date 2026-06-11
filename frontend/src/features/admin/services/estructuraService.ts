import { api } from '@/shared/services/api'
import type {
  Carrera,
  CreateCarreraPayload,
  UpdateCarreraPayload,
  Cohorte,
  CreateCohortePayload,
  UpdateCohortePayload,
  Materia,
  CreateMateriaPayload,
  UpdateMateriaPayload,
} from '../types'

// ─── Carreras ─────────────────────────────────────────────────────────────────

export async function fetchCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[]>('/v1/admin/carreras')
  return data
}

export async function createCarrera(payload: CreateCarreraPayload): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/v1/admin/carreras', payload)
  return data
}

export async function updateCarrera(id: string, payload: UpdateCarreraPayload): Promise<Carrera> {
  const { data } = await api.put<Carrera>(`/v1/admin/carreras/${id}`, payload)
  return data
}

export async function deleteCarrera(id: string): Promise<void> {
  await api.delete(`/v1/admin/carreras/${id}`)
}

// ─── Cohortes ─────────────────────────────────────────────────────────────────

export async function fetchCohortes(): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[]>('/v1/admin/cohortes')
  return data
}

export async function createCohorte(payload: CreateCohortePayload): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/v1/admin/cohortes', payload)
  return data
}

export async function updateCohorte(id: string, payload: UpdateCohortePayload): Promise<Cohorte> {
  const { data } = await api.put<Cohorte>(`/v1/admin/cohortes/${id}`, payload)
  return data
}

export async function deleteCohorte(id: string): Promise<void> {
  await api.delete(`/v1/admin/cohortes/${id}`)
}

// ─── Materias ─────────────────────────────────────────────────────────────────

export async function fetchMaterias(): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/v1/admin/materias')
  return data
}

export async function createMateria(payload: CreateMateriaPayload): Promise<Materia> {
  const { data } = await api.post<Materia>('/v1/admin/materias', payload)
  return data
}

export async function updateMateria(id: string, payload: UpdateMateriaPayload): Promise<Materia> {
  const { data } = await api.put<Materia>(`/v1/admin/materias/${id}`, payload)
  return data
}

export async function deleteMateria(id: string): Promise<void> {
  await api.delete(`/v1/admin/materias/${id}`)
}
