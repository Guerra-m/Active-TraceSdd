export interface MenuItem {
  label: string
  path: string
  permission: string
  icon?: string
}

export const MENU_ITEMS: MenuItem[] = [
  { label: 'Dashboard', path: '/dashboard', permission: 'dashboard:read' },
  { label: 'Alumnos', path: '/alumnos', permission: 'alumnos:read' },
  { label: 'Materias', path: '/materias', permission: 'materias:read' },
  { label: 'Comisiones', path: '/comisiones', permission: 'comisiones:read' },
  { label: 'Comunicaciones', path: '/comunicacion', permission: 'comunicacion:read' },
  { label: 'Equipos docentes', path: '/equipos', permission: 'equipos:read' },
  { label: 'Encuentros', path: '/encuentros', permission: 'encuentros:read' },
  { label: 'Coloquios', path: '/coloquios', permission: 'coloquios:read' },
  { label: 'Liquidaciones', path: '/liquidaciones', permission: 'liquidaciones:read' },
  { label: 'Auditoría', path: '/auditoria', permission: 'auditoria:read' },
  { label: 'Usuarios', path: '/usuarios', permission: 'usuarios:read' },
  // Módulo académico docente (C-22)
  { label: 'Atrasados', path: '/profesor/atrasados', permission: 'atrasados:ver' },
  { label: 'Importar calificaciones', path: '/profesor/importar', permission: 'atrasados:ver' },
  { label: 'Umbral', path: '/profesor/umbral', permission: 'atrasados:ver' },
  { label: 'Entregas sin corregir', path: '/profesor/entregas', permission: 'atrasados:ver' },
  { label: 'Enviar comunicaciones', path: '/profesor/comunicaciones', permission: 'comunicacion:enviar' },
  { label: 'Monitor', path: '/profesor/monitor', permission: 'atrasados:ver' },
  // Coordinación (C-23)
  { label: 'Equipos (coord)', path: '/equipos', permission: 'equipos:asignar' },
  { label: 'Avisos', path: '/avisos', permission: 'avisos:publicar' },
  { label: 'Tareas', path: '/tareas', permission: 'tareas:gestionar' },
  { label: 'Monitor coordinación', path: '/monitor', permission: 'atrasados:ver' },
  { label: 'Encuentros (admin)', path: '/encuentros/admin', permission: 'encuentros:gestionar' },
  { label: 'Coloquios (coord)', path: '/coloquios', permission: 'coloquios:read' },
  { label: 'Setup cuatrimestre', path: '/setup-cuatrimestre', permission: 'equipos:asignar' },
  // Finanzas (C-24)
  { label: 'Liquidaciones', path: '/finanzas/liquidaciones', permission: 'liquidaciones:ver' },
  { label: 'Grilla salarial', path: '/finanzas/grilla-salarial', permission: 'liquidaciones:gestionar' },
  { label: 'Facturas', path: '/finanzas/facturas', permission: 'liquidaciones:ver' },
  // Administración (C-24)
  { label: 'Estructura académica', path: '/admin/estructura', permission: 'estructura:gestionar' },
  { label: 'Usuarios (admin)', path: '/admin/usuarios', permission: 'estructura:gestionar' },
  { label: 'Auditoría', path: '/admin/auditoria', permission: 'auditoria:ver' },
]
