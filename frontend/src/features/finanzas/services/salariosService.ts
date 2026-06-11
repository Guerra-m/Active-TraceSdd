import { api } from '@/shared/services/api'
import type {
  SalarioBase,
  SalarioPlus,
  CreateSalarioBasePayload,
  UpdateSalarioBasePayload,
  CreateSalarioPlusPayload,
  UpdateSalarioPlusPayload,
} from '../types'

// ─── Salario Base ─────────────────────────────────────────────────────────────

export async function fetchSalariosBase(): Promise<SalarioBase[]> {
  const { data } = await api.get<SalarioBase[]>('/v1/salarios/base')
  return data
}

export async function createSalarioBase(payload: CreateSalarioBasePayload): Promise<SalarioBase> {
  const { data } = await api.post<SalarioBase>('/v1/salarios/base', payload)
  return data
}

export async function updateSalarioBase(
  id: string,
  payload: UpdateSalarioBasePayload,
): Promise<SalarioBase> {
  const { data } = await api.put<SalarioBase>(`/v1/salarios/base/${id}`, payload)
  return data
}

// ─── Salario Plus ─────────────────────────────────────────────────────────────

export async function fetchSalariosPlus(): Promise<SalarioPlus[]> {
  const { data } = await api.get<SalarioPlus[]>('/v1/salarios/plus')
  return data
}

export async function createSalarioPlus(payload: CreateSalarioPlusPayload): Promise<SalarioPlus> {
  const { data } = await api.post<SalarioPlus>('/v1/salarios/plus', payload)
  return data
}

export async function updateSalarioPlus(
  id: string,
  payload: UpdateSalarioPlusPayload,
): Promise<SalarioPlus> {
  const { data } = await api.put<SalarioPlus>(`/v1/salarios/plus/${id}`, payload)
  return data
}
