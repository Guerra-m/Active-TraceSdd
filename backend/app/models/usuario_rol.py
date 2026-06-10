"""Modelo ORM para la asignación UsuarioRol con vigencia temporal.

Asigna roles a usuarios dentro de un tenant con fechas de vigencia explícitas.

Decisión D3 del design:
  - valid_from DATE NOT NULL: fecha de inicio de vigencia
  - valid_until DATE nullable: NULL = vigencia abierta (indefinida)
  - La vigencia es el mecanismo de expiración — NO soft delete
  - Las asignaciones vencidas se conservan para auditoría histórica

NOTA: TenantScopedBase tiene deleted_at para soft delete, pero UsuarioRol
NO usa el mecanismo de soft delete — la columna deleted_at existe por
herencia pero la vigencia (valid_from/valid_until) es el control de acceso.

Restricción: UNIQUE (user_id, rol_id, tenant_id, valid_from) para evitar
asignaciones duplicadas con la misma fecha de inicio.
"""

from datetime import datetime, timezone

from sqlalchemy import UUID as SAUUID, Column, Date, ForeignKey, Index, UniqueConstraint

from app.core.database import Base
from app.models.base import TenantScopedBase


class UsuarioRol(TenantScopedBase, Base):
    """Asignación temporal de un rol a un usuario dentro de un tenant."""

    __tablename__ = "usuario_rol"

    # user_id: FK a users
    user_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # rol_id: FK a roles
    rol_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # valid_from: inicio de vigencia (obligatorio)
    valid_from = Column(
        Date,
        nullable=False,
    )

    # valid_until: fin de vigencia (NULL = abierta, indefinida)
    valid_until = Column(
        Date,
        nullable=True,
        default=None,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "rol_id", "tenant_id", "valid_from",
            name="uq_usuario_rol_vigencia",
        ),
        Index("ix_usuario_rol_user_tenant", "user_id", "tenant_id", "valid_from", "valid_until"),
    )

    def __repr__(self) -> str:
        return (
            f"<UsuarioRol user={self.user_id} rol={self.rol_id} "
            f"from={self.valid_from} until={self.valid_until}>"
        )
