"""Modelo ORM para PasswordResetToken.

Token de recuperación de contraseña de un solo uso.
- El token crudo se envía por email al usuario.
- En DB solo se guarda el hash SHA-256.
- Expira en 1 hora máximo (regla de seguridad).
- Una vez usado, used_at se setea y el token no puede reutilizarse.

Campos:
  - id        : UUID v4 PK
  - user_id   : FK → users.id
  - tenant_id : row-level tenancy
  - token_hash: SHA-256 del token (UNIQUE, indexado)
  - expires_at: timestamp UTC de expiración (máx 1h desde creación)
  - used_at   : timestamp UTC de uso (NULL = no usado)
  - created_at: timestamp UTC de creación
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy import UUID as SAUUID

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PasswordResetToken(Base):
    """Token de recuperación de contraseña, un solo uso, expiración 1h."""

    __tablename__ = "password_reset_tokens"

    id = Column(
        SAUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # FK al usuario propietario
    user_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Row-level tenancy — obligatorio
    tenant_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # SHA-256 del token crudo — nunca el valor original
    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Expiración UTC (máx 1h desde creación)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Marca de uso — NULL = no usado; datetime = ya utilizado
    used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # Timestamp de creación
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("ix_prt_tenant_user", "tenant_id", "user_id"),
    )

    def is_valid(self) -> bool:
        """True si el token no fue usado y no expiró."""
        now = datetime.now(timezone.utc)
        return self.used_at is None and self.expires_at > now

    def __repr__(self) -> str:
        return f"<PasswordResetToken id={self.id} user={self.user_id} used={self.used_at is not None}>"
