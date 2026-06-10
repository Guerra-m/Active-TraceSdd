"""Schemas Pydantic para el catálogo RBAC.

Todos los schemas siguen la regla dura #5: extra='forbid'.
Esto garantiza que ningún campo no declarado sea aceptado ni devuelto.

Schemas de respuesta (GET):
  - RolResponse       : datos públicos de un rol
  - PermisoResponse   : datos públicos de un permiso
  - RolPermisoResponse: permiso dentro de un rol con su flag is_own_resource
  - UsuarioRolResponse: asignación de rol a usuario con vigencia
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RolResponse(BaseModel):
    """Datos públicos de un Rol."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    code: str
    name: str
    is_system: bool
    is_active: bool


class PermisoResponse(BaseModel):
    """Datos públicos de un Permiso."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    code: str
    description: str


class RolPermisoResponse(BaseModel):
    """Permiso asignado a un rol con su flag is_own_resource."""

    model_config = ConfigDict(extra="forbid")

    permiso: PermisoResponse
    is_own_resource: bool


class UsuarioRolResponse(BaseModel):
    """Asignación de rol a un usuario con vigencia temporal."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    rol: RolResponse
    valid_from: date
    valid_until: date | None
