"""Excepciones y handlers estandarizados de la aplicacion.

RESERVADO para C-02+ (handlers de errores de dominio y HTTP).

Este modulo implementara:
  - Excepciones de dominio base (DomainError, NotFoundError, ConflictError, etc.)
  - Exception handlers de FastAPI para respuestas HTTP estandarizadas
  - Handler para ValidationError de Pydantic → 422 con cuerpo estructurado
  - Handler para errores de tenancy y RBAC → 403/404 sin revelar info de otros tenants
  - Formato de error estandar: {"code": "...", "message": "...", "details": [...]}
"""

# RESERVADO → C-02+
