"""Modelo ORM para la entidad Rol.

Rol define una función dentro del sistema (ALUMNO, TUTOR, PROFESOR, etc.).
Los roles del dominio son globales (is_system=True, tenant_id=NULL).
Los roles custom son por tenant (is_system=False, tenant_id=uuid).

No hereda TenantScopedBase porque los roles del sistema no pertenecen a
ningún tenant específico. Lleva tenant_id nullable explícito.

Decisión D6 del design: Rol y Permiso heredan Base directamente.
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import UUID as SAUUID, Boolean, Column, DateTime, ForeignKey, Index, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Rol(Base):
    """Rol del dominio o custom por tenant.

    - is_system=True, tenant_id=NULL  → roles del dominio (no modificables)
    - is_system=False, tenant_id=uuid → roles custom creados por un tenant
    """

    __tablename__ = "roles"

    id = Column(
        SAUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Código único del rol (e.g. "ALUMNO", "PROFESOR")
    code = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    # Nombre legible del rol
    name = Column(
        String(255),
        nullable=False,
    )

    # True = rol del dominio (seed, no modificable); False = custom por tenant
    is_system = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
    )

    # NULL para roles del sistema; UUID del tenant para roles custom
    tenant_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

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

    # Soft delete — NULL = activo
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        Index("ix_roles_code", "code", unique=True),
        Index("ix_roles_tenant_id", "tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<Rol code={self.code!r} system={self.is_system} tenant={self.tenant_id}>"
