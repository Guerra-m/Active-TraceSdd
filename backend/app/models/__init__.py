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
from app.models.slot_encuentro import SlotEncuentro
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.guardia import Guardia
from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
from app.models.aviso import Aviso, AcknowledgmentAviso
from app.models.tarea import Tarea, ComentarioTarea
from app.models.programa_materia import FechaAcademica, ProgramaMateria
from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.models.salario import SalarioBase, SalarioPlus
from app.models.liquidacion import Liquidacion
from app.models.factura import Factura

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
    "SlotEncuentro",
    "InstanciaEncuentro",
    "Guardia",
    "Evaluacion",
    "ReservaEvaluacion",
    "ResultadoEvaluacion",
    "Aviso",
    "AcknowledgmentAviso",
    "Tarea",
    "ComentarioTarea",
    "FechaAcademica",
    "ProgramaMateria",
    "HiloMensaje",
    "MensajeInterno",
    "SalarioBase",
    "SalarioPlus",
    "Liquidacion",
    "Factura",
]
