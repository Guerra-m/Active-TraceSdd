"""Modelo ORM para RefreshToken.

Almacena el hash SHA-256 del refresh token (nunca el valor crudo).
El token crudo se emite UNA sola vez en la respuesta HTTP y nunca
se persiste. La rotación revoca el token viejo inmediatamente.

Campos:
  - id          : UUID v4 PK
  - user_id     : FK → users.id
  - tenant_id   : UUID (row-level tenancy — todos los queries filtran por tenant)
  - token_hash  : SHA-256 del token crudo (UNIQUE, indexado)
  - expires_at  : timestamp UTC de expiración
  - revoked_at  : timestamp UTC de revocación (NULL = vigente)
  - created_at  : timestamp UTC de creación

Regla de rotación (design D2):
  - Al usar un refresh token → se revoca (revoked_at = now) y se emite uno nuevo.
  - Un token revocado nunca puede usarse de nuevo.
  - Un token ya expirado es rechazado aunque no esté revocado.

Nota (design D6): No hereda TenantScopedBase para evitar conflicto con el
mixin (que no incluye user_id), pero SÍ incluye tenant_id explícitamente
para cumplir row-level tenancy.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy import UUID as SAUUID

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RefreshToken(Base):
    """Token de refresh con rotación. Solo el hash se persiste."""

    __tablename__ = "refresh_tokens"

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

    # Row-level tenancy — obligatorio (regla dura #9)
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

    # Expiración UTC
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Revocación — NULL = vigente; datetime = revocado
    revoked_at = Column(
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
        Index("ix_refresh_tokens_tenant_user", "tenant_id", "user_id"),
    )

    def is_valid(self) -> bool:
        """True si el token no está revocado y no expiró."""
        now = datetime.now(timezone.utc)
        return self.revoked_at is None and self.expires_at > now

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user={self.user_id} revoked={self.revoked_at is not None}>"
