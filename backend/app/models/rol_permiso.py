"""Modelo ORM para la tabla de unión RolPermiso.

Asocia un Rol con un Permiso dentro de un tenant, con el flag is_own_resource
que indica si el permiso aplica solo sobre recursos propios del usuario.

Decisión D2 del design:
  is_own_resource=True  → el permiso aplica solo sobre los propios recursos
  is_own_resource=False → acceso global al permiso

Decisión D6:
  Hereda TenantScopedBase porque la asignación rol↔permiso es tenant-specific.
  (Restricción: UNIQUE en (rol_id, permiso_id, tenant_id))

NOTA sobre tenant_id:
  El seed de la matriz base usa tenant_id=NULL (roles del sistema son globales).
  Las asignaciones de roles custom por tenant tendrán tenant_id concreto.
  Por esto, tenant_id es nullable=True aquí (override del TenantScopedBase).
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import UUID as SAUUID, Boolean, Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import declared_attr

from app.core.database import Base
from app.models.base import TenantScopedBase


class RolPermiso(TenantScopedBase, Base):
    """Asignación de un permiso a un rol dentro de un tenant."""

    __tablename__ = "rol_permiso"

    # Override tenant_id: nullable=True para permitir el seed global (tenant_id=NULL)
    @declared_attr
    def tenant_id(cls):  # noqa: N805
        return Column(
            SAUUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=True,  # NULL = asignación del sistema (seed base)
            index=True,
        )

    # rol_id: FK a roles
    rol_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # permiso_id: FK a permisos
    permiso_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("permisos.id", ondelete="CASCADE"),
        nullable=False,
    )

    # is_own_resource: True = permiso aplica solo sobre recursos propios
    is_own_resource = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
    )

    __table_args__ = (
        UniqueConstraint("rol_id", "permiso_id", "tenant_id", name="uq_rol_permiso_tenant"),
        Index("ix_rol_permiso_rol_tenant", "rol_id", "tenant_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<RolPermiso rol={self.rol_id} permiso={self.permiso_id} "
            f"tenant={self.tenant_id} own={self.is_own_resource}>"
        )
