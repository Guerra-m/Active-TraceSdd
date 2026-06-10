"""Modelo ORM para la entidad User (usuario del sistema).

User hereda TenantScopedBase: id UUID, tenant_id, created_at, updated_at, deleted_at.

Campos sensibles:
  - email_encrypted : email cifrado con AES-256-GCM (via core/encryption.py)
  - email_hash      : SHA-256 del email normalizado — indexado para búsquedas eficientes
  - password_hash   : hash Argon2id del password (nunca texto plano)
  - totp_secret_encrypted: secreto TOTP cifrado (NULL si 2FA no habilitado)
  - totp_enabled    : flag de 2FA activo
  - dni_encrypted, cuil_encrypted, cbu_encrypted, alias_cbu_encrypted: PII cifrada AES-256-GCM

El email NO se almacena en texto plano por privacidad (PII). Las búsquedas
usan email_hash (determinístico). El email legible se obtiene descifrando
email_encrypted cuando es necesario.

Regla dura #12: PII (email, totp_secret, dni, cuil, cbu) siempre AES-256. Passwords con Argon2id.
Regla dura #14: identidad por UUID interno — email es atributo de negocio, no credencial de sesión.
"""

from sqlalchemy import Boolean, CheckConstraint, Column, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class User(TenantScopedBase, Base):
    """Entidad usuario de active-trace. Pertenece a un tenant.

    Nunca acceder a *_encrypted directamente — usar métodos del UserRepository
    que gestionan cifrado/descifrado. El __repr__ omite PII intencionalmente.
    """

    __tablename__ = "users"

    # --- Auth ---
    email_encrypted = Column(String, nullable=False)
    email_hash = Column(String(64), nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    totp_secret_encrypted = Column(String, nullable=True, default=None)
    totp_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    # --- Perfil docente ---
    nombre = Column(String(200), nullable=True)
    apellidos = Column(String(200), nullable=True)
    banco = Column(String(100), nullable=True)
    regional = Column(String(100), nullable=True)
    legajo = Column(String(50), nullable=True)
    legajo_profesional = Column(String(50), nullable=True)
    facturador = Column(Boolean, nullable=False, default=False, server_default="false")
    estado = Column(String(20), nullable=False, default="Activo", server_default="Activo")

    # --- PII cifrada (AES-256-GCM) — nunca texto plano en DB ---
    dni_encrypted = Column(Text, nullable=True)
    cuil_encrypted = Column(Text, nullable=True)
    cbu_encrypted = Column(Text, nullable=True)
    alias_cbu_encrypted = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_users_tenant_email_hash", "tenant_id", "email_hash", unique=True),
        CheckConstraint("estado IN ('Activo', 'Inactivo')", name="ck_users_estado"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant={self.tenant_id} estado={self.estado}>"
