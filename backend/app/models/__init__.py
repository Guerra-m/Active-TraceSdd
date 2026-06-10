"""Modelos ORM de active-trace.

Importar desde este paquete para registrar todos los modelos
en Base.metadata antes de ejecutar migraciones Alembic.
"""

from app.models.asignacion import Asignacion
from app.models.comunicacion import Comunicacion
from app.models.lote_comunicacion import LoteComunicacion
from app.models.audit_log import AuditLog
from app.models.calificacion import Calificacion
from app.models.umbral_materia import UmbralMateria
from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.models.base import TenantScopedBase
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
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
    "Asignacion",
    "Comunicacion",
    "LoteComunicacion",
    "AuditLog",
    "Calificacion",
    "UmbralMateria",
    "EntradaPadron",
    "VersionPadron",
    "Carrera",
    "Cohorte",
    "Materia",
    "Tenant",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "Rol",
    "Permiso",
    "RolPermiso",
    "UsuarioRol",
]
