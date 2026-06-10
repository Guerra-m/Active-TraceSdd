"""Modelo ORM para la entidad Tenant (institucion educativa).

Tenant es la raiz del sistema de multi-tenancy. NO hereda TenantScopedBase
porque es la entidad que define el scope — no pertenece a ningun tenant.

Campos:
  - id         : UUID v4 PK, generado en Python
  - name       : nombre institucional, unico, no vacio
  - slug       : identificador URL-safe (kebab-case), unico, no vacio
  - is_active  : booleano, True por defecto — permite deshabilitar un tenant
  - created_at : timestamp UTC de creacion
  - updated_at : timestamp UTC de ultima modificacion

Decision D1 del design: Tenant usa Base directamente, sin mixin.
No tiene tenant_id ni deleted_at (la gestion de tenants es administrativa).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy import UUID as SAUUID

from app.core.database import Base


def _utcnow() -> datetime:
    """Devuelve el momento actual en UTC (aware)."""
    return datetime.now(timezone.utc)


class Tenant(Base):
    """Entidad raiz del sistema — representa una institucion educativa."""

    __tablename__ = "tenants"

    # PK: UUID v4 generado en Python (Decision D2)
    id = Column(
        SAUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Nombre institucional — debe ser unico y no vacio
    name = Column(
        String(255),
        nullable=False,
        unique=True,
    )

    # Slug URL-safe — usado en URLs y como identificador legible
    slug = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    # Estado activo — False permite deshabilitar sin borrar
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Timestamps de auditoria
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r} active={self.is_active}>"
