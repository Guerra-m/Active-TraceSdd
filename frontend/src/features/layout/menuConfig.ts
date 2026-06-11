export interface MenuItem {
  label: string
  path: string
  permission: string
  icon?: string
}

export const MENU_ITEMS: MenuItem[] = [
  // General — todos los usuarios autenticados
  { label: 'Dashboard', path: '/dashboard', permission: 'perfil:editar' },

  // Módulo académico docente (C-22) — PROFESOR / TUTOR / COORDINADOR
  { label: 'Importar / Padrón', path: '/profesor/importar', permission: 'padron:importar' },
  { label: 'Atrasados', path: '/profesor/atrasados', permission: 'atrasados:ver' },
  { label: 'Umbral', path: '/profesor/umbral', permission: 'atrasados:ver' },
  { label: 'Entregas sin corregir', path: '/profesor/entregas', permission: 'entregas:ver' },
  { label: 'Enviar comunicaciones', path: '/profesor/comunicaciones', permission: 'comunicacion:enviar' },
  { label: 'Monitor docente', path: '/profesor/monitor', permission: 'atrasados:ver' },

  // Coordinación (C-23) — COORDINADOR / ADMIN
  { label: 'Materias', path: '/materias', permission: 'estructura:gestionar' },
  { label: 'Alumnos (Padrón)', path: '/alumnos', permission: 'padron:importar' },
  { label: 'Comisiones', path: '/comisiones', permission: 'equipos:asignar' },
  { label: 'Equipos docentes', path: '/equipos', permission: 'equipos:asignar' },
  { label: 'Avisos', path: '/avisos', permission: 'avisos:publicar' },
  { label: 'Tareas', path: '/tareas', permission: 'tareas:gestionar' },
  { label: 'Monitor coordinación', path: '/monitor', permission: 'atrasados:ver' },
  { label: 'Encuentros', path: '/encuentros/admin', permission: 'encuentros:gestionar' },
  { label: 'Coloquios', path: '/coloquios', permission: 'coloquios:gestionar' },
  { label: 'Setup cuatrimestre', path: '/setup-cuatrimestre', permission: 'equipos:asignar' },

  // Finanzas (C-24) — FINANZAS
  { label: 'Liquidaciones', path: '/finanzas/liquidaciones', permission: 'liquidaciones:operar' },
  { label: 'Grilla salarial', path: '/finanzas/grilla-salarial', permission: 'liquidaciones:operar' },
  { label: 'Facturas', path: '/finanzas/facturas', permission: 'facturas:gestionar' },

  // Administración (C-24) — ADMIN / COORDINADOR
  { label: 'Estructura académica', path: '/admin/estructura', permission: 'estructura:gestionar' },
  { label: 'Usuarios', path: '/admin/usuarios', permission: 'usuarios:gestionar' },
  { label: 'Auditoría', path: '/admin/auditoria', permission: 'auditoria:ver' },
]
