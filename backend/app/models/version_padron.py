"""Modelo ORM para VersionPadron (C-09 padron-ingesta-moodle).

Cada importación de padrón crea una nueva VersionPadron.
Solo una versión puede estar activa por (tenant_id, materia_id, cohorte_id)
en simultáneo. Al activar una nueva, la anterior se desactiva (activa=False).
Las versiones anteriores se conservan para auditoría (nunca se borran).
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class VersionPadron(TenantScopedBase, Base):
    """Cabecera de una versión de padrón importada para materia×cohorte."""

    __tablename__ = "version_padron"

    materia_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cargado_por = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cargado_at = Column(DateTime(timezone=True), nullable=False)
    activa = Column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        Index("ix_version_padron_tenant", "tenant_id"),
        Index("ix_version_padron_tenant_materia_cohorte", "tenant_id", "materia_id", "cohorte_id"),
        Index("ix_version_padron_tenant_activa", "tenant_id", "materia_id", "cohorte_id", "activa"),
    )

    def __repr__(self) -> str:
        return (
            f"<VersionPadron id={self.id} materia={self.materia_id} "
            f"cohorte={self.cohorte_id} activa={self.activa}>"
        )
