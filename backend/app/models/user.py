"""Modelo ORM para la entidad User (usuario del sistema).

User hereda TenantScopedBase: id UUID, tenant_id, created_at, updated_at, deleted_at.

Campos sensibles:
  - email_encrypted : email cifrado con AES-256-GCM (via core/encryption.py)
  - email_hash      : SHA-256 del email normalizado — indexado para búsquedas eficientes
  - password_hash   : hash Argon2id del password (nunca texto plano)
  - totp_secret_encrypted: secreto TOTP cifrado (NULL si 2FA no habilitado)
  - totp_enabled    : flag de 2FA activo

El email NO se almacena en texto plano por privacidad (PII). Las búsquedas
usan email_hash (determinístico). El email legible se obtiene descifrando
email_encrypted cuando es necesario.

Regla dura #12: PII (email, totp_secret) siempre AES-256. Passwords con Argon2id.
Regla dura #14: identidad por UUID interno — email es atributo de negocio, no credencial de sesión.
"""

import uuid

from sqlalchemy import Boolean, Column, Index, String
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class User(TenantScopedBase, Base):
    """Entidad usuario de active-trace. Pertenece a un tenant.

    Nunca acceder a email_encrypted directamente — usar los métodos
    del UserRepository o del AuthService que gestionan cifrado/descifrado.
    """

    __tablename__ = "users"

    # Email cifrado con AES-256-GCM (PII — nunca en texto plano en DB)
    email_encrypted = Column(
        String,
        nullable=False,
    )

    # SHA-256 del email normalizado (lowercase + strip) — permite lookup O(1)
    # sin exponer el email. No es el email en texto plano.
    email_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Hash Argon2id del password (nunca texto plano, nunca otro algoritmo)
    password_hash = Column(
        String,
        nullable=False,
    )

    # Estado activo del usuario (False = cuenta deshabilitada)
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Secreto TOTP cifrado con AES-256-GCM (NULL si 2FA no configurado)
    totp_secret_encrypted = Column(
        String,
        nullable=True,
        default=None,
    )

    # Flag de 2FA habilitado (True = login requiere verificar TOTP)
    totp_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Índice compuesto tenant_id + email_hash para búsquedas multi-tenant eficientes
    __table_args__ = (
        Index("ix_users_tenant_email_hash", "tenant_id", "email_hash", unique=True),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant={self.tenant_id} active={self.is_active}>"
