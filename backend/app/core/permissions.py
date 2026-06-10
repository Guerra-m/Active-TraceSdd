"""Modulo de permisos — matriz RBAC fino modulo:accion.

RESERVADO para C-04 (RBAC).

Este modulo implementara:
  - Matriz de permisos por rol: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
  - Dependency require_permission(module, action) → 403 si no autorizado (fail-closed)
  - Resolucion de permisos desde la sesion autenticada del usuario (JWT)
  - Sin flags binarios ni superusuario; cada endpoint declara su permiso explicito

Reglas duras aplicables (ver CLAUDE.md):
  - RBAC fino modulo:accion, no flags binarios (#10)
  - Fail-closed: sin permiso explicito → 403 (#10)
  - Identidad SIEMPRE desde JWT, nunca desde parametros de request (#8)
"""

# RESERVADO → C-04
