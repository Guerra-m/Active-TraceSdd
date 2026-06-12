import type { LucideIcon } from 'lucide-react'
import { BookOpen, Users, Wallet, ShieldCheck } from 'lucide-react'

export interface MenuItem {
  label: string
  path: string
  permission: string
}

export interface MenuSection {
  id: string
  label: string
  icon: LucideIcon
  items: MenuItem[]
}

export const MENU_SECTIONS: MenuSection[] = [
  {
    id: 'academico',
    label: 'Académico',
    icon: BookOpen,
    items: [
      { label: 'Importar / Padrón', path: '/profesor/importar', permission: 'padron:importar' },
      { label: 'Atrasados', path: '/profesor/atrasados', permission: 'atrasados:ver' },
      { label: 'Umbral', path: '/profesor/umbral', permission: 'atrasados:ver' },
      { label: 'Entregas sin corregir', path: '/profesor/entregas', permission: 'entregas:ver' },
      { label: 'Comunicaciones', path: '/profesor/comunicaciones', permission: 'comunicacion:enviar' },
      { label: 'Monitor docente', path: '/profesor/monitor', permission: 'atrasados:ver' },
    ],
  },
  {
    id: 'coordinacion',
    label: 'Coordinación',
    icon: Users,
    items: [
      { label: 'Materias', path: '/materias', permission: 'estructura:gestionar' },
      { label: 'Alumnos', path: '/alumnos', permission: 'padron:importar' },
      { label: 'Comisiones', path: '/comisiones', permission: 'equipos:asignar' },
      { label: 'Equipos docentes', path: '/equipos', permission: 'equipos:asignar' },
      { label: 'Avisos', path: '/avisos', permission: 'avisos:publicar' },
      { label: 'Tareas', path: '/tareas', permission: 'tareas:gestionar' },
      { label: 'Monitor', path: '/monitor', permission: 'atrasados:ver' },
      { label: 'Encuentros', path: '/encuentros/admin', permission: 'encuentros:gestionar' },
      { label: 'Coloquios', path: '/coloquios', permission: 'coloquios:gestionar' },
      { label: 'Setup cuatrimestre', path: '/setup-cuatrimestre', permission: 'equipos:asignar' },
    ],
  },
  {
    id: 'finanzas',
    label: 'Finanzas',
    icon: Wallet,
    items: [
      { label: 'Liquidaciones', path: '/finanzas/liquidaciones', permission: 'liquidaciones:operar' },
      { label: 'Grilla salarial', path: '/finanzas/grilla-salarial', permission: 'liquidaciones:operar' },
      { label: 'Facturas', path: '/finanzas/facturas', permission: 'facturas:gestionar' },
    ],
  },
  {
    id: 'admin',
    label: 'Administración',
    icon: ShieldCheck,
    items: [
      { label: 'Estructura académica', path: '/admin/estructura', permission: 'estructura:gestionar' },
      { label: 'Usuarios', path: '/admin/usuarios', permission: 'usuarios:gestionar' },
      { label: 'Auditoría', path: '/admin/auditoria', permission: 'auditoria:ver' },
    ],
  },
]
