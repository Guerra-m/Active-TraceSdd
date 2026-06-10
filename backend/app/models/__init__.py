"""Modelos ORM de active-trace.

Importar desde este paquete para registrar todos los modelos
en Base.metadata antes de ejecutar migraciones Alembic.
"""

from app.models.base import TenantScopedBase
from app.models.password_reset_token import PasswordResetToken
from app.models.permiso import Permiso
from app.models.refresh_token import RefreshToken
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from app.models.usuario_rol import UsuarioRol

__all__ = [
    "TenantScopedBase",
    "Tenant",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "Rol",
    "Permiso",
    "RolPermiso",
    "UsuarioRol",
]
